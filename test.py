# from faiss_db import FaissDB
# from langchain_community.document_loaders import TextLoader
# text = TextLoader(r"C:\Users\itsup\Downloads\sample-text-file.txt").load()
# from langchain_huggingface import HuggingFaceEmbeddings
# faissdb = FaissDB()
# db = faissdb.load_vectordb()
# print(db.similarity_search_with_score("cat"))

from db_utilites.mongodb import MongoDB

db = MongoDB()
collection = db.get_collection(r"Pdf_Store")

