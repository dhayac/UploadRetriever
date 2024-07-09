from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from langchain_community.document_loaders import TextLoader
import numpy as np
from langchain_core.documents import Document
import faiss
import logger
class FaissDB:
    def __init__(self):
        self.embedding_name = "all-MiniLM-L6-v2"
        #self.text  = TextLoader(r"D:\fastapi\documents\Car.txt", encoding="utf-8").load()[0].page_content
    def __create_vectordb(self):
        with open(r"D:\fastapi\documents\Car.txt",encoding="utf-8") as f:
            self.text = f.read()
        self.topic = "Car"
        self.doument_embeddings = self.embeddings.embed_documents([self.text])
        self.document = Document(page_content=self.text, metadata = {"topic": self.topic})
        self.db = FAISS.from_documents([self.document],embedding=self.embeddings)
        self.db.save_local(r"D:\fastapi\vectorstore")
    
    
    def load_vectordb(self):
        self.db = FAISS.load_local(r"D:\fastapi\vectorstore", self.embeddings,allow_dangerous_deserialization=True)   
        return self.db
    
    async def add_document(self,content: str, metadata: dict[str,str]) -> None:
        try:
            document = [Document(content,metadata = metadata)]
            self.db.aadd_documents(document)
            logger.info("document added to faissdb")
        except Exception as exe:
            logger.error(f"Error during add document in faissdb {exe}")
    

    def save_local(self,):
        try:
            self.db.save_local(r"D:\fastapi\vectorstore")
            logger.info("Vector DB saved in local")
        except Exception as exe:
            logger.error(f"Error during save vector in local: message {exe}")
    
    async def initialize(self):
        self.embeddings = HuggingFaceEmbeddings(model_name=self.embedding_name)