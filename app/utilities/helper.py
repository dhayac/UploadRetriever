import os
import time

import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from pymongo.collection import Collection

from app.utilities import dc_logger
from app.utilities.singletons_factory import DcSingleton
from app.utilities.dc_exception import FileNotFoundException

logger  = dc_logger.LoggerAdap(dc_logger.get_logger(__name__),{"vectordb":"faiss"})

class Helper(metaclass = DcSingleton):
    
    @staticmethod
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
            os.remove(path)
            logger.info("Removed temprory File")
            return text
        except Exception as exe:
            logger.info(f"Error in parsing pdf {exe}")
            raise exe
        
    @staticmethod
    def save_pdf(tmp_path: str, content: bytes, filename: str) -> str:
        try:
            if not os.path.exists(tmp_path):
                    os.mkdir(tmp_path)
            path = os.path.join(tmp_path, filename)
            with open(path, 'wb') as f:
                f.write(content)
            return path
        except Exception as exe:
              logger.error("Error occcured in save pdf")
              raise exe 
    
    @staticmethod
    def create_chunk(file_id: str, file_name: str, text: str):
        textsplitter = RecursiveCharacterTextSplitter(chunk_size = 1000,chunk_overlap=0)
        doc = Document(page_content = text, metadata = {"fileid":file_id,"filename":file_name})
        chunk_doc = textsplitter.split_documents([doc])
        return chunk_doc
    
    @staticmethod
    def checkfiles_db(collection: Collection, file_id: str) -> dict:
        query = {"file_id": file_id}
        result = collection.find_one(query)
        if not result:
            raise FileNotFoundException(f"File id is not found in data base: {file_id}")
        else:
            return result
        
    @staticmethod
    async def update_vectorid(collection: Collection, file_id: str, vector_ids):
        try:
            update_result = collection.update_one({"file_id":file_id},{"$set":{"vector_ids":vector_ids}})
            if update_result.modified_count == 0:
                 raise Exception("vector id is not updates in document")
        except Exception as exe:
             logger.info(f"Error occured update vector ids {exe}")
             raise exe