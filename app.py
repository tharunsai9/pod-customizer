from fastapi import FastAPI
from pydantic import BaseModel
import requests, os, fitz
from PIL import Image

app=FastAPI()
TEMP_FOLDER="temp"; OUTPUT_FOLDER="output"
os.makedirs(TEMP_FOLDER,exist_ok=True); os.makedirs(OUTPUT_FOLDER,exist_ok=True)

class PODRequest(BaseModel):
    row_number:int
    SessionID:str
    FileName:str
    FileURL:str
    FileType:str
    TemplateName:str
    StockColor:str
    Size:str
    Ink:str
    Sides:str
    Orientation:str
    Collate:str
    FitPaper:str
    PaperType:str
    Stapling:str
    Folding:str
    Lamination:str
    TabPaperType:str
    CreateTabsOnline:str
    TabsIncluded:str
    ComposeTabs:str

@app.get("/")
def root():
    return {"status":"running"}

@app.post("/customize")
def customize(data:PODRequest):
    name=f"{data.FileName}.{data.FileType}"
    temp=os.path.join(TEMP_FOLDER,name)
    r=requests.get(data.FileURL,timeout=60); r.raise_for_status()
    open(temp,"wb").write(r.content)
    if data.FileType.lower()=="pdf":
        doc=fitz.open(temp)
        out=os.path.join(OUTPUT_FOLDER,data.SessionID+".pdf")
        doc.save(out); doc.close()
    else:
        img=Image.open(temp).convert("RGB").resize((1080,670))
        if data.Ink=="Black and White":
            img=img.convert("L").convert("RGB")
        if data.Orientation=="Landscape":
            img=img.rotate(90,expand=True)
        out=os.path.join(OUTPUT_FOLDER,data.SessionID+".png")
        img.save(out)
    return {"success":True,"SessionID":data.SessionID,"OutputFile":out}
