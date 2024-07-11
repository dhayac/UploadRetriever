
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from logger import get_logger
import hashlib
from gridfs import GridFS
from pymongo.database import Database

logger = get_logger()
uri = "mongodb://localhost:27017/"


# Create a new client and connect to the server
class MongoDB:
    def __init__(self):  
        self.client = MongoClient(uri, server_api=ServerApi('1'))

        # Send a ping to confirm a successful connection
        try:
            self.client.admin.command('ping')
            logger.info("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            logger.error(f"Error during pinging error: {e}")


    def get_collection(self, collection_name: str, database_name: str):
        try:
            db = self.client.get_database(database_name)

            collection = db.get_collection(collection_name)
            return db,collection
        except Exception as e:
            logger.error(f"Error in get Collection {e}")
    
    @staticmethod
    def check_fileid(fileid: str, collection):
        result = collection.find({"fileid":f"{fileid}"})
        output = []
        for r in result:
            output.append(r)
        return output
    
    def add_files(self,content: str,fileid: str, topic: str, filename: str,collection,db):
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
                "hash" : md5.hexdigest(),
                "fs_id" : fs_id}
            collection.insert_one(metadata)
            logger.info("Sucessfully added to collection")
            return {"message": f"Sucessfully added to collection {filename}"}
        except Exception as exe:
            logger.error(f"Error during adding files to mongoDB: {exe}")
            return {"error": str(exe)}, 500


    
        
