
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from app.utilities import s_logger
import hashlib
from gridfs import GridFS
from pymongo.collection import Collection
from pymongo.database import Database

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
            logger.error(f"Error in get Collection {e}")
    
    @staticmethod
    def check_fileid(fileid: str, collection):
        result = collection.find({"fileid":f"{fileid}"})
        output = []
        for r in result:
            output.append(r)
        return output
    
    def add_files(self,content: str,fileid: str, topic: str, filename: str,collection, vector_id):
        try:
            griddb = self.client.get_database("Gridfs")
            fs = GridFS(griddb, collection=fileid)
            md5 = hashlib.md5()
            md5.update(content)
            fs_id = fs.put(content, fileid = fileid)
            
            metadata = {
                "filename": filename,
                "fileid": fileid,
                "topic": topic,
                #"hash" : md5.hexdigest(),
                "fs_id" : fs_id,
                "vector_id":vector_id}
            
            collection.insert_one(metadata)
            logger.info("Sucessfully added to collection")
            return f"Sucessfully added to collection {filename}"
        except Exception as exe:
            logger.error(f"Error during adding files to mongoDB: {exe}")
            return {"error": str(exe)}, 500
        
    def mongo_retrive(self, collection, fileids: list[str]):

        cursors = [collection.find({"fileid":fileid}) for fileid in fileids]
        metadata = []
        for cursor in cursors:
            for post in cursor:
                metadata.append(post)
        if len(metadata) == 0:
            return "No files found"
        else:
            return metadata


    
        
