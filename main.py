from enum import Enum
import time 
import asyncio
from fastapi import FastAPI, Request, Form, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles 
from fastapi.templating import Jinja2Templates
from faiss_db import FaissDB
import asyncio
from contextlib import asynccontextmanager
from logger import get_logger
import json
import PyPDF2
from io import BytesIO
import requests
from db_utilites.mongodb import MongoDB

db = MongoDB()
collection = db.get_collection(r"Pdf_Store")
logger = get_logger()
app = FastAPI()
template = Jinja2Templates(directory= r"D:\fastapi\templates")
faiss_db = FaissDB()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the background task to initialize FaissDB
    background_tasks = BackgroundTasks()
    background_tasks.add_task(faiss_db.initialize)
    # print("hi")
    logger.info(f"Started background task to initialize FaissDB {faiss_db}")
    yield
    # Cleanup if needed
    logger.info("Lifespan context manager exited")

app.router.lifespan_context = lifespan
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



# @app.get("/uploadfile", response_class=HTMLResponse)
# async def uploadfile(request: Request):
#     #if not file:
#     #    return {"no file"}
#     #else:
#     #    contents = await file.read()
#     #    return {"contents":contents}
#     return template.TemplateResponse(request= request, name = "upload.html")

# @app.post("/processfile", response_class=HTMLResponse)
# async def uploadfile(request: Request, file: UploadFile= File(...)):
#     if not file:
#         return {"message":"file not found"}
#     else:
#         return {"message": type(file)}


@app.post("/process_pdf_file/")
async def process_pdf_file(file_id: str, file_topic: str, file: UploadFile = File(...) ,):
    # Save file locally for processing
    contents = await file.read()
    # with open(file.filename, 'wb') as f:
    #     f.write(contents)
    
    # Process saved file
    return await process_pdf(file.filename, is_local_file=True)

async def process_pdf(pdf_source, is_local_file=False):

    file = BytesIO(requests.get(pdf_source).content) if not is_local_file else open(pdf_source, 'rb')

    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page_no in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page_no].extract_text()
    
    if is_local_file:
        file.close()


    return text

async def add_collection(content,fileid,topic,collection):
    db.add_files(content=content,)
    return