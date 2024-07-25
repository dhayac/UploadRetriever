import time 
import os
import base64

from fastapi import APIRouter, HTTPException, status, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.services.vector_db_services.faiss_db import FaissDB
from app.utilities.helper import Helper
from app.utilities import dc_logger
from app.utilities.db_utilities.mongodb import MongoDB
from app.utilities.constants import Constants
from app.utilities import dc_logger
from app.utilities.dc_exception import VectoridNotFoundException, FileNotFoundException

logger = dc_logger.LoggerAdap(dc_logger.get_logger(__name__),{"vectordb": "faiss"})

router = APIRouter(
    tags= ["Inference"],
    responses={status.HTTP_404_NOT_FOUND: {"description":"notfound"}}
)
logger.info("vectordb router is initialized")

mongodb = MongoDB()
bookdb, collection = mongodb.get_db_collection(database_name=Constants.fetch_constant("mongodb")["db_name"], collection_name=Constants.fetch_constant("mongodb")["collection_name"])
faiss_db = FaissDB()
faiss_db.load_vectordb()
tempelates_dir = Constants.fetch_constant("templates")["path"]
template = Jinja2Templates(directory=tempelates_dir )

def handle_500_error(response_data):
    return JSONResponse(status.HTTP_500_INTERNAL_SERVER_ERROR, 
                        content=response_data)

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
            path = Helper.save_pdf(tmp_path, content=content_bytes, filename= file.filename)
            text = Helper.parse_pdf(path) 
            #mongodb
            content = base64.b64encode(content_bytes)
            message, condition = mongodb.add_files(content=content,fileid=file_id, filename= file_name, 
                              topic=file_topic, author=file_author,collection=collection)
            
            chunk_doc = Helper.create_chunk(file_id, file_name=file_name, text= text)
            #faiss
            if condition:
                vector_ids = await faiss_db.add_document(chunks = chunk_doc, metadata= {"fileid":file_id,"topic":file_topic})
                # upload_result = collection.update_one({"file_id":file_id},{"$set":{"vector_ids":vector_ids}})
                Helper.checkfiles_db(collection, file_id)
                await Helper.update_vectorid(collection, file_id, vector_ids)
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
    
@router.post("/delete")
async def delete(request: Request, file_id: str = Form(...)):
    try:
        #check
        result_mongo = Helper.checkfiles_db(collection=collection, file_id=file_id)
        vector_ids = result_mongo["vector_ids"]
        result_faiss = faiss_db.check_document(vector_ids)
        
        #delete doc
        if result_faiss and result_mongo:
            await faiss_db.delete_document(vector_ids)
            mongodb.delete_doc(collection=collection, file_id=file_id)
            mongodb.delete_gridfs(file_id=file_id)
            faiss_db.save_local()
            return {
            "status": True,
            "file_id": file_id,
            "message": "File deleted"}
    
    except VectoridNotFoundException as exe:
        raise HTTPException(status_code = exe.get_code(), 
                            detail= {
                                "status": "Failed",
                                "file_id": file_id,
                                "error": exe.get_message()
                            })
    except FileNotFoundException as exe:
        raise HTTPException(status_code = exe.get_code(), 
                        detail= {
                            "status": "Failed",
                            "file_id": file_id,
                            "error": exe.get_message()
                        })
    except Exception as exe:
        raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail={
                                "status": "Failed",
                                "file_id": file_id,
                                "error": exe.__str__()
                            })
