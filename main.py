from enum import Enum
import time 
import asyncio
from fastapi import FastAPI, Request, Form
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles 
from fastapi.templating import Jinja2Templates

app = FastAPI()
template = Jinja2Templates(directory= r"D:\fastapi\templates")
@app.get("/")
async def root():
    return {"message":"hello world"}

# @app.post("/upload")
# def upload_file(fileid: str):
#     print(f"file {fileid} i uploading")
#     time.sleep(5)
#     print(f"file uploaded: id--> {fileid}")
#     return {"message":f"file_id: {fileid}"}

@app.get("/mainpage", response_class=HTMLResponse)
async def mainpage(request: Request ):
    return template.TemplateResponse(request=request, name = "main.html")

@app.post("/sucess",response_class=HTMLResponse)
async def sucesspage(request: Request, id: str = Form(None)):
    if id:
        print("ID: ", id)
        return template.TemplateResponse(request= request, name = "sucess.html")
    else:
        return template.TemplateResponse(request= request, name = "main.html")