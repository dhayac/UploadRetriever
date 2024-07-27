import hashlib
from gridfs import GridFS
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.collection import Collection
from pymongo.database import Database

from app.utilities.env_util import EnvironmentVariableRetriever
from app.utilities import dc_logger
from app.utilities.dc_exception import FileNotFoundException

logger = dc_logger.LoggerAdap(dc_logger.get_logger(__name__),{"vectordb":"faiss"})
uri= EnvironmentVariableRetriever.get_env_variable("MONGO_URI")

class MongoDB:
    def __init__(self):  
        self.client = MongoClient(uri, server_api=ServerApi('1'))
        try:
            self.client.admin.command('ping')
            logger.info("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            logger.error(f"Error during pinging error: {e}")
            raise e

    def get_db_collection(self, collection_name: str, database_name: str) -> tuple[Database, Collection]:
        try:
            db = self.client.get_database(database_name)

            collection = db.get_collection(collection_name)
            return db, collection
        except Exception as e:
            logger.error(f"Error in get db and Collection {e}")
            raise e
    
    @staticmethod
    def check_fileid(file_id: str, collection):
        result = collection.find({"file_id":f"{file_id}"})
        output = []
        for r in result:
            output.append(r)
        return output
    
    @staticmethod
    def chech_hash(hash: str, collection):
        """
            Check if a given hash exists in the specified collection.
        Returns:
            bool: True if the hash exists in the collection, False otherwise.
        """
        result = collection.find({"hash":hash})
        output = []
        for r in result:
            output.append(r)
        if len(output) != 0:
            return True
        else:
            return False

    def add_files(self,content: str,fileid: str, topic: str, filename: str,author: str,collection):
        try:
            md5 = hashlib.md5()
            md5.update(content)
            hash = md5.hexdigest()
            if not MongoDB.chech_hash(hash, collection=collection):
                griddb = self.client.get_database("Gridfs")
                fs = GridFS(griddb, collection=fileid)
                fs_id = fs.put(content, fileid = fileid)
                metadata = {
                    "file_id": fileid,
                    "name": filename,
                    "author": author,
                    "topic": topic,
                    "hash" : hash,
                    "fs_id" : fs_id}
                collection.insert_one(metadata)
                logger.info("Sucessfully added to collection")
                return f"Sucessfully added to collection: {filename}", True
            else:
                return f"File is already in db: {filename}", False
        except Exception as exe:
            logger.error(f"Error during adding files to mongoDB: {exe}")
            return "Error occured during adding files", False
               
    def mongo_retrive(self, collection: Collection, fileids: list[str]|str, scores: list):
        try:
            if type(fileids)==  str:
                fileids = [fileids]
            cursors = [collection.find({"file_id":fileid}) for fileid in fileids]
            metadata = []
            for n, cursor in enumerate(cursors):
                dic = {}
                for post in cursor:
                    dic["file_id"] = post["file_id"]
                    dic["name"] = post["name"]
                    dic["author"] = post["author"]
                    dic["topic"] = post["topic"]
                    dic["score"] = scores[n]
                if len(dic) != 0:
                    metadata.append(dic)
            return metadata
        except Exception as exe:
            logger.error(f"Error during retrivel {exe}", exc_info= True)
            raise exe
    
    @staticmethod
    def delete_doc(collection: Collection, file_id: str):
        try:
            query = {"file_id": file_id}
            result_doc = collection.delete_one(query)
            if result_doc:
                logger.info("Successfully data deleted in mongo db")
                return result_doc
        except Exception as exe:
            logger.warning(f"Data Deletion Failed {exe}", exc_info=True)
            raise  exe
    
    def delete_gridfs(self, file_id: str) -> None:
        try:
            db_name = "Gridfs"
            collection_name_chunks = f"{file_id}.chunks"
            # delete chunks
            db, collection = self.get_db_collection(database_name = db_name, collection_name=collection_name_chunks)
            collection.drop()
            # delete files
            collection_name_files = f"{file_id}.files"
            db, collection = self.get_db_collection(database_name = db_name, collection_name=collection_name_files)
            collection.drop()
            logger.info(f"GridFs Deleted Sucessfully: {file_id}")
        except Exception as exe:
            logger.error(f"An error occurred during the deletion of GridFS")
            raise  exe