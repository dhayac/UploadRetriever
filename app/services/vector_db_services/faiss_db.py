import warnings

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from app.services.vector_db_services.vector_db_interface import VectorDBInterface
from app.utilities import dc_logger
from app.utilities.constants import Constants


# Suppress all UserWarnings
warnings.filterwarnings("ignore", category=UserWarning)

logger = dc_logger.LoggerAdap(dc_logger.get_logger(__name__), {"vectordb":"faiss"})

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
            raise exe
    
    def save_local(self):
        try:
            self.db.save_local(Constants.fetch_constant("faissdb")["path"])
            logger.info("Vector DB saved in local")
        except Exception as exe:
            logger.error(f"Error during save vector in local: message {exe}")
            raise exe
    
    async def add_document(self,chunks: list[Document], metadata: dict[str,str]) -> list[str]:
        try:
            message = await self.db.aadd_documents(documents=chunks, metadata = metadata)
            logger.info("document added to faissdb")
            return message
        except Exception as exe:
            logger.error(f"Error during add document in faissdb {exe}")
            raise exe
    
    async def delete_document(self, vectorids)-> bool | None:
        try:
            result = await self.db.adelete(vectorids)
            logger.info("Document Successfully deleted in faiss db")
        except Exception as e:
            logger.error(f"Error occured while delete document: {result}")
            raise e
    
    async def run_query(self, query: str) :
        retriever = self.db.as_retriever(search_type="similarity_score_threshold", search_kwargs={'score_threshold': 0.4})
        result = await retriever.ainvoke(input = query)
        fileids = []
        for doc in result:
            if doc.metadata["fileid"] not in fileids:
                fileids.append(doc.metadata["fileid"])
        return fileids
    

        