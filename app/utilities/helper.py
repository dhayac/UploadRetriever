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
        
        """
        Parse a PDF file and extract its text content, then remove the temporary file.

        Args:
            path (str): The path to the PDF file to be parsed.

        Returns:
            str: The extracted text content from the PDF.

        Raises:
        Exception: If there is an error in parsing the PDF file.
        
        """
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
        """
        Save a PDF file from binary content to a specified temporary path.

        Args:
            tmp_path (str): The temporary path to save the PDF file.
            content (bytes): The binary content of the PDF file.
            filename (str): The name of the PDF file.

        Returns:
            str: The path where the PDF file is saved.

        Raises:
            Exception: If there is an error saving the PDF file.
        """
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
    def create_chunk(file_id: str, file_name: str, text: str) -> list[Document]:
        """
        Create chunks of a document using a text splitter.

        Args:
            file_id (str): The ID of the file.
            file_name (str): The name of the file.
            text (str): The text content to be split into chunks.

        Returns:
            list[Document]: A list of Document objects representing the chunks.
        """
        textsplitter = RecursiveCharacterTextSplitter(chunk_size = 1500,chunk_overlap=0)
        doc = Document(page_content = text, metadata = {"fileid":file_id,"filename":file_name})
        chunk_doc = textsplitter.split_documents([doc])
        return chunk_doc

    @staticmethod
    async def update_vectorid(collection: Collection, file_id: str, vector_ids):
        
        """
        Update the vector IDs in the database for a specific file.

        Args:
            collection (Collection): The MongoDB collection to update.
            file_id (str): The ID of the file to update.
            vector_ids: The new vector IDs to set for the file.

        Raises:
            Exception: If the vector ID is not updated in the document.
            Exception: If there is an error updating the vector IDs.
        """
        try:
            update_result = collection.update_one({"file_id":file_id},{"$set":{"vector_ids":vector_ids}})
            if update_result.modified_count == 0:
                 raise Exception("vector id is not updates in document")
        except Exception as exe:
             logger.info(f"Error occured update vector ids {exe}")
             raise exe
        
    @staticmethod
    async def files_count(collection: Collection) -> int:
        """
        Count the number of files in the collection.

        Args:
            collection (Collection): The MongoDB collection to query.

        Returns:
            int: The number of files in the collection.

        Raises:
            Exception: If there is an error counting the files.
        """
        try:
            lst = list(collection.find())
            return len(lst)
        except Exception as exe:
            raise exe
    
    @staticmethod
    def find_files(file_id, collection: Collection):
        
        """
        Find files in the collection by file ID.

        Args:
            file_id: The ID of the file to find.
            collection (Collection): The MongoDB collection to query.

        Returns:
            list: A list of documents matching the file ID.
        """
        result = collection.find({"file_id":file_id})
        output = []
        for r in result:
            output.append(r)
        return output
    
    @staticmethod
    def check_document(vectordb, vector_ids) -> bool:
        """
        Check if all vector IDs exist in the vector database.
    
        Args:
            vectordb: The vector database to check.
            vector_ids: The vector IDs to verify.
    
        Returns:
            bool: True if all vector IDs are present, False otherwise.
        """
        for vector_id in vector_ids:
            if vector_id not in list(vectordb.index_to_docstore_id.values()):
                return False
        else:
            return True