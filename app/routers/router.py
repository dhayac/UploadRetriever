import time 
import os
import base64

from fastapi import APIRouter, HTTPException, status,FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

from app.services.vector_db_services.faiss_db import FaissDB
from app.utilities import s_logger
from app.utilities.db_utilities.mongodb import MongoDB
from app.utilities.constants import Constants
from app.utilities import s_logger
from app.utilities.processpdf import parse_pdf


logger = s_logger.LoggerAdap(s_logger.get_logger(__name__),{"vectordb": "faiss"})

router = APIRouter(
    tags= ["Inference"],
    responses={status.HTTP_404_NOT_FOUND: {"description":"notfound"}}
)
logger.info("vectordb router is initialized")

mongodb = MongoDB()
bookdb, collection = mongodb.get_collection(database_name=Constants.fetch_constant("mongodb")["db_name"], collection_name=Constants.fetch_constant("mongodb")["collection_name"])
faiss_db = FaissDB()
faiss_db.load_vectordb()
tempelates_dir = Constants.fetch_constant("templates")["path"]
template = Jinja2Templates(directory=tempelates_dir )


@router.get("/")
async def root():
    return {"status":"healthy"}

@router.get("/mainpage", response_class=HTMLResponse)
async def mainpage(request: Request ):
    return template.TemplateResponse(request=request, name = Constants.fetch_constant("templates")["main"])

@router.get("/upload", response_class=HTMLResponse)
async def uploadfile(request: Request):
    return template.TemplateResponse(request= request, name = Constants.fetch_constant("templates")["upload"])

@router.post("/processfile",response_class=HTMLResponse)
async def process_pdf_file(request: Request, file_id: str = Form(...), file_name: str = Form(...), 
                           file_topic: str = Form(...), file_author: str = Form(...), file: UploadFile = File(...)):
    # Save file locally for processing
    try:
        if len(MongoDB.check_fileid(file_id=file_id, collection  = collection))==0:
            content_bytes = await file.read()
            tmp_path= Constants.fetch_constant("tmp")["path"]
            if not os.path.exists(tmp_path):
                os.mkdir(tmp_path)
            path = os.path.join(tmp_path,file.filename)
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
                upload_result = collection.update_one({"file_id":file_id},{"$set":{"vector_ids":vector_ids}})
                faiss_db.save_local()
            
            
            return template.TemplateResponse(name = Constants.fetch_constant("templates")["processfile"], 
                                         context={"request":request, "file_id": file_id,
                                                  "file_name":file_name,
                                                  "file_topic":file_topic,
                                                  "file_author":file_author,
                                                  "upload_status": message})
        
        else:
            return template.TemplateResponse(name = Constants.fetch_constant("templates")["processfile"], 
                                         context={"request":request, "file_id": file_id,
                                                  "file_name":file_name,
                                                  "file_topic":file_topic,
                                                  "file_author":file_author,
                                                  "upload_status": "File id is already available in db"})
        #return data
    except Exception as exe:
        logger.error("Error exe")
        return {"error":str(exe)}, 500

@router.get("/query", response_class=HTMLResponse)
async def query(request: Request):
    return template.TemplateResponse(request, name = Constants.fetch_constant("templates")["query"])

@router.post("/queryresult", response_class=HTMLResponse)
async def querydoc(request: Request, query: str = Form(...)):
    try:
        result_faiss = faiss_db.run_query(query)
        if len(result_faiss)> 0:
            fileids = list(result_faiss.keys())
            scores = list(result_faiss.values())
            metadata_mongodb = mongodb.mongo_retrive( collection = collection,fileids=fileids, scores = scores)

            # return metadata_mongodb
            return template.TemplateResponse(name =Constants.fetch_constant("templates")["queryresult"],context={"request":request,
                                                                           "query": query,
                                                                            "results":metadata_mongodb})
        else: 
            return template.TemplateResponse(name =Constants.fetch_constant("templates")["queryresult"],context={"request":request,
                                                                           "query": query,
                                                                            "results":[]})
    except Exception as exe:
        return {"error": str(exe)}, 500