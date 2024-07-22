from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from app.services.vector_db_services.vector_db_interface import VectorDBInterface
from app.utilities import s_logger
from app.utilities.constants import Constants
from app.utilities.dc_exception import VectoridNotFoundException

logger = s_logger.LoggerAdap(s_logger.get_logger(__name__), {"vectordb":"faiss"})

class FaissDB(VectorDBInterface):
    
    def __init__(self):
        self.embedding_path = Constants.fetch_constant("embedding_model")["path"]
        self.embeddings = HuggingFaceEmbeddings(model_name=self.embedding_path)
    
    def __create_vectordb(self):
        with open(r"D:\fastapi\documents\Car.txt",encoding="utf-8") as f:
            self.text = f.read()
        self.topic = "Car"
        self.doument_embeddings = self.embeddings.embed_documents([self.text])
        self.document = Document(page_content=self.text, metadata = {"topic": self.topic})
        self.db = FAISS.from_documents([self.document],embedding=self.embeddings)
        self.db.save_local(r"D:\fastapi\vectorstore")
    
    def load_vectordb(self):
        try:
            self.db = FAISS.load_local(Constants.fetch_constant("faissdb")["path"], self.embeddings,allow_dangerous_deserialization=True)
        except Exception as exe:
            logger.error(f"Error in load_vectordb {exe}")
    
    def save_local(self):
        try:
            self.db.save_local(Constants.fetch_constant("faissdb")["path"])
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
    
    async def delete_document(self, vectorids)-> bool | None:
        try:
            result = self.db.delete(vectorids)
            logger.info("Document Successfully deleted in faiss db")
        except Exception as e:
            logger.error(f"Error occured while delete document: {result}")
    
    def run_query(self, query: str) :
        results_with_scores = self.db.similarity_search_with_score(query, k=Constants.fetch_constant("faissdb")["k"])
        dic = {}
        for doc, score in results_with_scores:
            if f"{doc.metadata["fileid"]}" not in dic.keys():
                dic[f"{doc.metadata["fileid"]}"] = [score]
            else:
                dic[f"{doc.metadata["fileid"]}"].append(score)
        data = {key:min(value) for key,value in dic.items()}
        return data
    
    def check_document(self, vector_ids) -> bool:
        for vector_id in vector_ids:
            if vector_id not in list(self.db.index_to_docstore_id.values()):
                raise VectoridNotFoundException(f"Vectors is not found in vector db ")
        else:
            return True
    async def check_doc_count(self):
        pass