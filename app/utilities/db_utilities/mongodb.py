
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from app.utilities import s_logger
import hashlib
from gridfs import GridFS

logger = s_logger.LoggerAdap(s_logger.get_logger(__name__),{"vectordb":"faiss"})
uri = "mongodb://localhost:27017/"


class MongoDB:
    def __init__(self):  
        self.client = MongoClient(uri, server_api=ServerApi('1'))
        try:
            self.client.admin.command('ping')
            logger.info("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            logger.error(f"Error during pinging error: {e}")


    def get_collection(self, collection_name: str, database_name: str):
        try:
            db = self.client.get_database(database_name)

            collection = db.get_collection(collection_name)
            return db, collection
        except Exception as e:
            logger.error(f"Error in get db and Collection {e}")
    
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
        
    def mongo_retrive(self, collection, fileids: list[str]|str, scores: list):
        try:
            if type(fileids)==  str:
                fileids = [fileids]
            cursors = [collection.find({"file_id":fileid}) for fileid in fileids]
            metadata = []
            for cursor in cursors:
                dic = {}
                for post in cursor:
                    dic["file_id"] = post["file_id"]
                    dic["name"] = post["name"]
                    dic["author"] = post["author"]
                    dic["topic"] = post["topic"]
                if len(dic) != 0:
                    metadata.append(dic)
            return metadata
            # if len(metadata) == 0:
            #     return "No files found"
            # else:
        except Exception as exe:
            logger.error(f"Error during retrivel {exe}")

    
        
