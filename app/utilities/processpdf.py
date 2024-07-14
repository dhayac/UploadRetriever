import pdfplumber
from langchain_text_splitters import CharacterTextSplitter
from io import BytesIO
import requests
import time
from PyPDF2 import PdfReader
from app.utilities import s_logger
import os

logger  = s_logger.LoggerAdap(s_logger.get_logger(__name__),{"vectordb":"faiss"})
start = time.time

def parse_pdf(path: str):
            # with open(file.filename, 'wb') as f:
            #     f.write(contents)
            # Process saved file
            logger.info("Started Parsing pdf")
            start = time.time()
            with pdfplumber.open(path) as pdf:
                   text = ""
                   for n,page in enumerate(pdf.pages):
                        text += page.extract_text() + "\n"
                        logger.info(f"pg no {n}")
            
            logger.info(f"Time Taken for parsing pdf {time.time() - start}")
            print(time.time() - start)
            os.remove(path)
            logger.info("Removed temprory File")
            return text