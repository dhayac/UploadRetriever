# from app.utilities.faiss_db import FaissDB
# import asyncio
# from langchain_community.document_loaders import TextLoader
# text = TextLoader(r"C:\Users\itsup\Downloads\sample-text-file.txt").load()
# from langchain_huggingface import HuggingFaceEmbeddings
# faissdb = FaissDB()
# faissdb.initialize()

# db = faissdb.load_vectordb()
# # print(db.similarity_search_with_score("cat"))

# results_with_scores = faissdb.db.similarity_search_with_score("veicles")
# for doc, score in results_with_scores:
#     print(f"Metadata: {doc.metadata}, Score: {score}")
# # from db_utilites.mongodb import MongoDB
# # db = MongoDB()
# # collection = db.get_collection(r"Pdf_Store")

import pdfplumber
import time
start = time.time()
with pdfplumber.open(r"temp/deeplearning-ian_goodfellow.pdf") as pdf:
    text = ""
    
    for n,page in enumerate(pdf.pages):
        text += page.extract_text() + "\n"
        print(n)
end = time.time()
print(end-start)
#print(text)