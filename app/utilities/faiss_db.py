from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import numpy as np
from langchain_core.documents import Document
import faiss
from app.utilities.logger import get_logger
from pydantic import BaseModel


logger = get_logger()
class FaissDB:
    def __init__(self):
        self.embedding_name = "D:\\fastapi\\embedding_model\\all-mini-lm-l6-v2"
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
        self.db = FAISS.load_local(r"app/vectorstore", self.embeddings,allow_dangerous_deserialization=True)
    
    async def add_document(self,content: str, metadata: dict[str,str]) -> list[str]:
        try:
            document = [Document(content,metadata = metadata)]
            message = await self.db.aadd_documents(document)
            logger.info("document added to faissdb")
            return message
        except Exception as exe:
            logger.error(f"Error during add document in faissdb {exe}")
    
    def save_local(self):
        try:
            self.db.save_local(r"D:\fastapi\vectorstore")
            logger.info("Vector DB saved in local")
        except Exception as exe:
            logger.error(f"Error during save vector in local: message {exe}")
    
    def initialize(self):
        self.embeddings = HuggingFaceEmbeddings(model_name=self.embedding_name)
    
    def run_query(self, query: str) -> list[dict] :
        
        results_with_scores = self.db.similarity_search_with_score(query, k=3)
        results = []
        
        for doc,score in results_with_scores:
            results.append({"fileid": doc.metadata["fileid"], "score":score})
        
        return results