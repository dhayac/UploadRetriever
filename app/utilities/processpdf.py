import pdfplumber
from langchain_text_splitters import CharacterTextSplitter
from io import BytesIO
import requests
import time
from PyPDF2 import PdfReader
from app.utilities.logger import get_logger
import os
logger = get_logger()

def parse_pdf(path: str):
            # with open(file.filename, 'wb') as f:
            #     f.write(contents)
            # Process saved file
            start = time.time()
            with pdfplumber.open(path) as pdf:
                   text = ""
                   for n,page in enumerate(pdf.pages):
                        text += page.extract_text() + "\n"
                        logger.info(f"pg no {n}")
            
            logger.info(f"Time Taken for parsing pdf {time.time() - start}")
            os.remove(path)
            return text