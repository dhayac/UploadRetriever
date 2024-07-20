import time 
import os
import base64

from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

from app.routers.router import router
from app.utilities.processpdf import parse_pdf
from app.utilities.constants import Constants
from app.utilities import s_logger 

logger = s_logger.LoggerAdap(s_logger.get_logger(__name__),{"vectordb":"faiss"})

app = FastAPI()

@app.get("/")
async def root():
    return {"Server is On":"Status Healthy"}

subapi = FastAPI()
subapi.include_router(router)
app.mount("/vectordb/faiss", subapi)
logger.info("main intitialized")









    



