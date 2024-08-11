import warnings
import os

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from sentence_transformers import SentenceTransformer
from app.services.vector_db_services.vector_db_interface import VectorDBInterface
from app.utilities import dc_logger
from app.utilities.constants import Constants


# Suppress all UserWarnings
warnings.filterwarnings("ignore", category=UserWarning)

logger = dc_logger.LoggerAdap(dc_logger.get_logger(__name__), {"vectordb":"faiss"})

class FaissDB(VectorDBInterface):
    
    def __init__(self):
        self.embedding_path = Constants.fetch_constant("embedding_model")["path"]
        if not os.path.exists(self.embedding_path):
            logger.info(f"Model is not found Downloading...")
            model = SentenceTransformer(Constants.fetch_constant("embedding_model")["model"])
            os.makedirs(self.embedding_path, exist_ok=True)
            model.save(self.embedding_path)
            logger.info(f"Model Saved in {self.embedding_path}")
        self.embeddings = HuggingFaceEmbeddings(model_name=self.embedding_path)
    
    def create_vectordb(self):
        """
        Create a FAISS vector database by embedding documents using sample documents and saving the vector store locally.
        Suppresses all UserWarnings.
        Raises:
            Exception: If there is an error during the creation of the vector database.
        """
        try:
            with open(r"sample_documents\Dog.txt", encoding="utf-8") as f:
                self.sample1 = f.read()
            with open(r"sample_documents\Ferari.txt", encoding="utf-8") as f:
                self.sample2 = f.read()
            # Embed the documents
            self.embed1 = self.embeddings.embed_documents([self.sample1])[0]  # Get the first (and only) embedding
            self.embed2 = self.embeddings.embed_documents([self.sample2])[0]  # Get the first (and only) embedding

            # Create Document objects
            document1 = Document(page_content=self.sample1, metadata={"fileid": "sample:0", "topic": "sample:0"})
            document2 = Document(page_content=self.sample2, metadata={"fileid": "sample:1", "topic": "sample:1"})

            # Initialize FAISS vector store
            db = FAISS.from_documents([document1, document2], embedding=self.embeddings)

            # Save the FAISS vector store locally
            db.save_local(Constants.fetch_constant("faissdb")["path"])
        except Exception as exe:
            logger.info(f"Error occured creating vector db {exe}")
            raise exe
    
    def load_vectordb(self):
        
        """
        Load the FAISS vector database from a local path. If it doesn't exist, create it first.
        Raises:
            Exception: If there is an error loading the vector database.
        """       
        try:
            if not os.path.exists(Constants.fetch_constant("faissdb")["path"]):
                self.create_vectordb()
            self.db = FAISS.load_local(Constants.fetch_constant("faissdb")["path"], self.embeddings,allow_dangerous_deserialization=True)
        except Exception as exe:
            logger.error(f"Error in load_vectordb {exe}")
            raise exe
    
    def save_local(self):
        
        """
        Save the current FAISS vector database state to a local path.
        Raises:
            Exception: If there is an error during saving the vector database locally.

        """
        try:
            self.db.save_local(Constants.fetch_constant("faissdb")["path"])
            logger.info("Vector DB saved in local")
        except Exception as exe:
            logger.error(f"Error during save vector in local: message {exe}")
            raise exe
    
    async def add_document(self,chunks: list[Document], metadata: dict[str,str]) -> list[str]:
        """
        Add a document to the FAISS vector database asynchronously.

        Args:
            chunks (list[Document]): A list of Document objects to be added.
            metadata (dict[str, str]): Metadata associated with the documents.

        Returns:
            list[str]: Messages indicating the status of the operation.
        Raises:
            Exception: If there is an error adding the document to the FAISS vector database.
        """
    
        try:
            message = await self.db.aadd_documents(documents=chunks, metadata = metadata)
            logger.info("document added to faissdb")
            return message
        except Exception as exe:
            logger.error(f"Error during add document in faissdb {exe}")
            raise exe
    
    async def delete_document(self, vectorids)-> bool | None:

        """
        Delete a document from the FAISS vector database asynchronously.

        Args:
            vectorids: The vector IDs of the documents to be deleted.

        Returns:
            bool | None: A boolean indicating the success of the operation, or None.

        Raises:
            Exception: If there is an error deleting the document from the FAISS vector database.
        """
        try:
            result = await self.db.adelete(vectorids)
            logger.info("Document Successfully deleted in faiss db")
        except Exception as e:
            logger.error(f"Error occured while delete document: {result}")
            raise e
    
    async def run_query(self, query: str) :
        """
        Run a query against the FAISS vector database and return file IDs of similar documents.

        Args:
            query (str): The query string to search for.

        Returns:
            list[str]: A list of file IDs of the documents that are similar to the query.

        Raises:
            Exception: If there is an error running the query on the FAISS vector database.
        """
        retriever = self.db.as_retriever(search_type="similarity_score_threshold", search_kwargs={'score_threshold': Constants.fetch_constant("faissdb")["threshold"]})
        result = await retriever.ainvoke(input = query)
        fileids = []
        for doc in result:
            if doc.metadata["fileid"] not in fileids:
                fileids.append(doc.metadata["fileid"])
        return fileids
    

        