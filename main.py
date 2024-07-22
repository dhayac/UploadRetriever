from fastapi import FastAPI
from app.routers.router import router
from app.utilities import s_logger 

logger = s_logger.LoggerAdap(s_logger.get_logger(__name__),{"vectordb":"faiss"})

app = FastAPI()

@app.get("/")
async def root():
    return {"Server is On":"Status Healthy"}

subapi = FastAPI()
subapi.include_router(router)
app.mount("/vectordb/faiss", subapi)
logger.info("main intitialized")









    



