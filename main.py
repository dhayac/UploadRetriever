from enum import Enum
import time 
import asyncio
import os
from fastapi import FastAPI, Request, Form, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles 
from fastapi.templating import Jinja2Templates
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

from app.utilities.faiss_db import FaissDB
import asyncio
from contextlib import asynccontextmanager
from app.utilities import s_logger 
import json
import PyPDF2
from io import BytesIO
import requests
from PyPDF2 import PdfReader
from app.utilities.db_utilities.mongodb import MongoDB
import base64
import nest_asyncio
from app.utilities.processpdf import parse_pdf

mongodb = MongoDB()
bookdb, collection = mongodb.get_collection(database_name="BOOKS", collection_name="PdfStore")
logger = s_logger.LoggerAdap(s_logger.get_logger(__name__),{"vectordb":"faiss"})
app = FastAPI()
template = Jinja2Templates(directory= r"D:\fastapi\app\templates")
faiss_db = FaissDB()
faiss_db.initialize()
faiss_db.load_vectordb()



# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Start the background task to initialize FaissDB
#     background_tasks = BackgroundTasks()
#     background_tasks.add_task(faiss_db.initialize)
#     # print("hi")
#     logger.info(f"Started background task to initialize FaissDB {faiss_db}")
#     yield
#     # Cleanup if needed
#     logger.info("Lifespan context manager exited")

# app.router.lifespan_context = lifespan

@app.get("/")
async def root():
    return {"message":"hello world"}


@app.get("/mainpage", response_class=HTMLResponse)
async def mainpage(request: Request ):
    return template.TemplateResponse(request=request, name = "main.html")


# @app.post("/sucess",response_class=HTMLResponse)
# async def sucesspage(request: Request, id: str = Form(None)):
#     if id:
#         print("ID: ", id)
#         return template.TemplateResponse(request= request, name = "sucess.html")
#     else:
#         return template.TemplateResponse(request= request, name = "main.html")


@app.get("/upload", response_class=HTMLResponse)
async def uploadfile(request: Request):
    return template.TemplateResponse(request= request, name = "upload.html")


@app.post("/processfile/",response_class=HTMLResponse)
async def process_pdf_file(request: Request, file_id: str = Form(...), file_name: str = Form(...), 
                           file_topic: str = Form(...), file_author: str = Form(...), file: UploadFile = File(...)):
    # Save file locally for processing
    try:
        if len(MongoDB.check_fileid(file_id=file_id, collection  = collection))==0:
            content_bytes = await file.read()
            temp = r"D:\fastapi\temp"
            path = os.path.join(temp,file.filename)
            
            with open(path, 'wb') as f:
                f.write(content_bytes)

            text = parse_pdf(path=path)
            textsplitter = RecursiveCharacterTextSplitter(chunk_size = 1000,chunk_overlap=0)
            doc = Document(page_content = text, metadata = {"fileid":file_id,"filename":file_name})
            chunk_doc = textsplitter.split_documents([doc])
            

            #mongodb
            content = base64.b64encode(content_bytes)
            message,condition = mongodb.add_files(content=content,fileid=file_id, filename= file_name, 
                              topic=file_topic, author=file_author,collection=collection)
            
            #faiss
            if condition:
                vector_ids = await faiss_db.add_document(chunks = chunk_doc, metadata= {"fileid":file_id,"topic":file_topic})
                collection.update_one({"fileid":file_id},{"$set":{"vector_ids":vector_ids}})
                faiss_db.save_local()
            
            
            return template.TemplateResponse(name = "uploadmessage.html", 
                                         context={"request":request, "file_id": file_id,
                                                  "file_name":file_name,
                                                  "file_topic":file_topic,
                                                  "file_author":file_author,
                                                  "upload_status": message})
        
        else:
            return template.TemplateResponse(name = "uploadmessage.html", 
                                         context={"request":request, "file_id": file_id,
                                                  "file_name":file_name,
                                                  "file_topic":file_topic,
                                                  "file_author":file_author,
                                                  "upload_status": "File id is already available in db"})
        #return data
    except Exception as exe:
        logger.error("Error exe")
        return {"error":str(exe)}, 500


@app.get("/query", response_class=HTMLResponse)
async def query(request: Request):
    return template.TemplateResponse(request, name = "query.html")


@app.post("/queryprocess", response_class=HTMLResponse)
async def querydoc(request: Request, query: str = Form(...)):
    try:
        result_faiss = faiss_db.run_query(query)
        if len(result_faiss)> 0:
            fileids = list(result_faiss.keys())
            scores = list(result_faiss.values())
            metadata_mongodb = mongodb.mongo_retrive( collection = collection,fileids=fileids, scores = scores)

            # return metadata_mongodb
            return template.TemplateResponse(name ="queryresult.html",context={"request":request,
                                                                           "query": query,
                                                                            "results":metadata_mongodb})
        else: 
            return template.TemplateResponse(name ="queryresult.html",context={"request":request,
                                                                           "query": query,
                                                                            "results":[]})
    except Exception as exe:
        return {"error": str(exe)}, 500


