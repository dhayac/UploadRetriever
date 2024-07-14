from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import numpy as np
from langchain_core.documents import Document
import faiss
from app.utilities import s_logger
from pydantic import BaseModel
import os

logger = s_logger.LoggerAdap(s_logger.get_logger(__name__), {"vectordb":"faiss"})
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

    def save_local(self):
        try:
            # for file in os.listdir(r"D:\fastapi\vectorstore"):
            #     os.remove(os.path.join(r"D:\fastapi\vectorstore", file))
            self.db.save_local(r"app/vectorstore")
            logger.info("Vector DB saved in local")
        except Exception as exe:
            logger.error(f"Error during save vector in local: message {exe}")
    
    async def add_document(self,chunks: list[Document], metadata: dict[str,str]) -> list[str]:
        try:
            message = await self.db.aadd_documents(documents=chunks, metadata = metadata)
            logger.info("document added to faissdb")
            return message
        except Exception as exe:
            logger.error(f"Error during add document in faissdb {exe}")
    

    
    def initialize(self):
        self.embeddings = HuggingFaceEmbeddings(model_name=self.embedding_name)
    
    def run_query(self, query: str) :
        
        results_with_scores = self.db.similarity_search_with_score(query, k=3)

        dic = {}
        for doc, score in results_with_scores:
            if f"{doc.metadata["fileid"]}" not in dic.keys():
                dic[f"{doc.metadata["fileid"]}"] = [score]
            else:
                dic[f"{doc.metadata["fileid"]}"].append(score)
        data = {key:min(value) for key,value in dic.items()}
        return data