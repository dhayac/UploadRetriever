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
from app.utilities.logger import get_logger 
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
logger = get_logger()
app = FastAPI()
template = Jinja2Templates(directory= r"D:\fastapi\templates")
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

# @app.post("/upload")
# def upload_file(fileid: str):
#     print(f"file {fileid} i uploading")
#     time.sleep(5)
#     print(f"file uploaded: id--> {fileid}")
#     return {"message":f"file_id: {fileid}"}


@app.get("/mainpage", response_class=HTMLResponse)
async def mainpage(request: Request ):
    return template.TemplateResponse(request=request, name = "main.html")

@app.post("/sucess",response_class=HTMLResponse)
async def sucesspage(request: Request, id: str = Form(None)):
    if id:
        print("ID: ", id)
        return template.TemplateResponse(request= request, name = "sucess.html")
    else:
        return template.TemplateResponse(request= request, name = "main.html")



@app.get("/upload", response_class=HTMLResponse)
async def uploadfile(request: Request):
    return template.TemplateResponse(request= request, name = "upload.html")

# @app.post("/processfile", response_class=HTMLResponse)
# async def uploadfile(request: Request, file: UploadFile= File(...)):
#     if not file:
#         return {"message":"file not found"}
#     else:
#         return {"message": type(file)}


@app.post("/processfile/",response_class=HTMLResponse)
async def process_pdf_file(request: Request, file_id: str = Form(...), 
                           file_topic: str = Form(...), file: UploadFile = File(...)):
    # Save file locally for processing
    try:
        if len(MongoDB.check_fileid(fileid=file_id, collection  = collection))==0:
            content_bytes = await file.read()
            temp = r"D:\fastapi\temp"
            path = os.path.join(temp,file.filename)
            with open(path, 'wb') as f:
                f.write(content_bytes)
            # Process saved file
            #stream = BytesIO(content_bytes)
            text = parse_pdf(path=path)
            textsplitter = RecursiveCharacterTextSplitter(chunk_size = 1000,chunk_overlap=0)
            doc = Document(page_content = text, metadata = {"fileid":file_id,"filename":file.filename})
            chunk_doc = textsplitter.split_documents([doc])
            #faiss
            vector_id = await faiss_db.add_document(content = chunk_doc, metadata= {"fileid":file_id,"topic":file_topic})
            faiss_db.save_local()
            #mongodb
            content = base64.b64encode(content_bytes)
            message = mongodb.add_files(content=content,fileid=file_id, filename= file.filename, 
                              topic=file_topic, collection=collection,vector_id = vector_id[0])
            
            return template.TemplateResponse(name = "uploadmessage.html", 
                                         context={"request":request, "message":message})
        
        else:
            return template.TemplateResponse(name = "uploadmessage.html", 
                                         context={"request":request, "message":"fileid is already stored"})
        #return data
    except Exception as exe:
        return {"error":str(exe)}, 500

@app.post("/query", response_class=HTMLResponse)
async def querydoc(request: Request, query: str):

    result_faiss = faiss_db.run_query(query)

    fileids = [data["fileid"] for data in result_faiss]
    metadata_mongodb = mongodb.mongo_retrive( collection = collection,fileids=fileids)
    
    return metadata_mongodb

# async def store_vectordb(content, metadata):
#     faiss_db.add_document(content)
#     pass
# async def process_pdf(pdf_source):
    
#     with open(pdf_source, 'rb') as file:
#         pdf_reader = PyPDF2.PdfReader(file)
#         text = ""
#         for page_no in range(len(pdf_reader.pages)):
#             text += pdf_reader.pages[page_no].extract_text()
#     return text


