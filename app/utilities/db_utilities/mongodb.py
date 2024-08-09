import hashlib
from gridfs import GridFS
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.collection import Collection
from pymongo.database import Database
from bson.objectid import ObjectId

from app.utilities.env_util import EnvironmentVariableRetriever
from app.utilities import dc_logger
from app.utilities.constants import Constants
from app.utilities.helper import Helper
logger = dc_logger.LoggerAdap(dc_logger.get_logger(__name__),{"vectordb":"faiss"})
uri= EnvironmentVariableRetriever.get_env_variable("MONGO_URI")

class MongoDB:
    def __init__(self):  
        self.client = MongoClient(uri, server_api=ServerApi('1'))
        try:
            self.client.admin.command('ping')
            logger.info("Pinged your deployment. You successfully connected to MongoDB!")
            self.fs = GridFS(self.client.get_database(Constants.fetch_constant("mongodb")["db_name"]), 
                            collection=Constants.fetch_constant("mongodb")["collection_name"])
        except Exception as e:
            logger.error(f"Error during pinging error: {e}")
            raise e

    def get_db_metacollection(self, collection_name1: str, database_name: str,  collection_name2: str|None=None) -> tuple[Database, Collection]:
        
        """
        Retrieves a specific collection of gridf fs and 
        its corresponding database from MongoDB.

        Returns:
            tuple[Database, Collection]: A tuple containing the Database object and the Collection object.

        Raises:
            Exception: If there is an error in retrieving the database or collection.
        """
        try:
            db = self.client.get_database(database_name)
            collection1 = db.get_collection(collection_name1)
            if collection_name2:
                collection2 = db.get_collection(collection_name2)
                return collection1, collection2
            return db, collection1
        except Exception as e:
            logger.error(f"Error in get db and Collection {e}")
            raise e
    
    @staticmethod
    def check_hash(hash: str, collection: Collection):
        """
            Check if a given hash exists in the specified collection.
        Returns:
            bool: True if the hash exists in the collection, False otherwise.
        """
        result = collection.find({"md5":hash})
        output = []
        for r in result:
            output.append(r)
        if len(output) != 0:
            return True
        else:
            return False

    def add_files(self,content: str,fileid: str, topic: str, filename: str,author: str,collection):
        """
        Add a file to the MongoDB collection with metadata.
    
        Args:
            content (str): The content of the file to be added.
            fileid (str): The ID of the file.
            topic (str): The topic associated with the file.
            filename (str): The name of the file.
            author (str): The author of the file.
            collection: The MongoDB collection to add the file to.
    
        Returns:
            tuple[str, bool]: A message indicating the result of the operation and a boolean status.
    
        Raises:
            Exception: If there is an error during the process of adding the file to MongoDB.
        """
        try:
            md5 = hashlib.md5()
            md5.update(content)
            hash = md5.hexdigest()
            if not MongoDB.check_hash(hash, collection=collection):
                metadata = {
                    "file_id": fileid,
                    "name": filename,
                    "author": author,
                    "topic": topic,
                    "md5" : hash
                    }
                self.fs.put(content, **metadata)
                logger.info("Sucessfully added to collection")
                return f"Sucessfully added to collection: {filename}", True
            else:
                return f"File is already in db: {filename}", False
        except Exception as exe:
            logger.error(f"Error during adding files to mongoDB: {exe}")
            raise exe
    
    @staticmethod           
    def mongo_retrive(collection: Collection, fileids: list[str]|str, scores: list|None = None):
        
        """
        Retrieve metadata from a MongoDB collection for given file IDs.
    
        Args:
            collection (Collection): The MongoDB collection to query.
            fileids (list[str] | str): A list of file IDs or a single file ID to retrieve metadata for.
            scores (list | None, optional): A list of scores corresponding to the file IDs. Defaults to None.
    
        Returns:
            list[dict]: A list of dictionaries containing metadata for each file ID.
    
        Raises:
            Exception: If there is an error during retrieval.
        """

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
                    if scores:
                        dic["score"] = scores[n]
                    else:
                        dic["score"] = scores
                if len(dic) != 0:
                    metadata.append(dic)
            return metadata
        except Exception as exe:
            logger.error(f"Error during retrivel {exe}", exc_info= True)
            raise exe
    
    def delete_doc(self,metadata_collection: Collection, file_id: str):
        """
        Delete a document from the MongoDB collection based on file ID.

        Args:
            metadata_collection (Collection): The MongoDB collection containing metadata.
            file_id (str): The ID of the file to delete.

        Raises:
            FileNotFoundError: If the file is not found in the collection.
            Exception: If there is an error during the deletion process.
        """
        try:
            result = Helper.find_files(file_id=file_id,collection=metadata_collection)
            if len(result)>0:
                obj_id = result[0]["_id"]
                self.fs.delete(file_id=obj_id)
            else:
                raise FileNotFoundError(f"File is not found ")
        except Exception as exe:
            logger.warning(f"Data Deletion Failed {exe}", exc_info=True)
            raise  exe