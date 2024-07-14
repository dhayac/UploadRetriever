import pdfplumber
import time
from app.utilities import s_logger
import os

logger  = s_logger.LoggerAdap(s_logger.get_logger(__name__),{"vectordb":"faiss"})
start = time.time

def parse_pdf(path: str):
          try:
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
          
          except Exception as exe:
                 logger.info(f"Error in parsing pdf {exe}")
            