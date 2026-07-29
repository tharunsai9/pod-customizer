from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests
import fitz
from PIL import Image
import cloudinary
import cloudinary.uploader

# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI()

# -----------------------------
# Configure Cloudinary
# -----------------------------
CLOUDINARY_URL=cloudinary://756848288755769:UcxDBJ-AN-yca2SAGuTtSBVLmXw@penyjj7h
cloudinary.config(
    cloudinary_url=os.getenv("CLOUDINARY_URL")
)

# -----------------------------
# Folders
# -----------------------------
TEMP_FOLDER = "temp"
OUTPUT_FOLDER = "output"

os.makedirs(TEMP_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# -----------------------------
# Request Model
# -----------------------------
class PODRequest(BaseModel):
    row_number: int
    SessionID: str
    FileName: str
    FileURL: str
    FileType: str
    TemplateName: str
    StockColor: str
    Size: str
    Ink: str
    Sides: str
    Orientation: str
    Collate: str
    FitPaper: str
    PaperType: str
    Stapling: str
    Folding: str
    Lamination: str
    TabPaperType: str
    CreateTabsOnline: str
    TabsIncluded: str
    ComposeTabs: str


# -----------------------------
# Health Check
# -----------------------------
@app.get("/")
def root():
    return {"status": "running"}


# -----------------------------
# Customize Endpoint
# -----------------------------
@app.post("/customize")
def customize(data: PODRequest):

    try:

        filename = f"{data.FileName}.{data.FileType}"
        temp_path = os.path.join(TEMP_FOLDER, filename)

        # Download file
        response = requests.get(data.FileURL, timeout=60)
        response.raise_for_status()

        with open(temp_path, "wb") as f:
            f.write(response.content)

        # -----------------------------
        # Process PDF
        # -----------------------------
        if data.FileType.lower() == "pdf":

            doc = fitz.open(temp_path)

            output_path = os.path.join(
                OUTPUT_FOLDER,
                f"{data.SessionID}.pdf"
            )

            doc.save(output_path)
            doc.close()

            upload_result = cloudinary.uploader.upload(
                output_path,
                resource_type="raw",
                folder="POD_Output"
            )

        # -----------------------------
        # Process Image
        # -----------------------------
        else:

            img = Image.open(temp_path).convert("RGB")
            img = img.resize((1080, 670))

            if data.Ink == "Black and White":
                img = img.convert("L").convert("RGB")

            if data.Orientation == "Landscape":
                img = img.rotate(90, expand=True)

            output_path = os.path.join(
                OUTPUT_FOLDER,
                f"{data.SessionID}.png"
            )

            img.save(output_path)

            upload_result = cloudinary.uploader.upload(
                output_path,
                resource_type="image",
                folder="POD_Output"
            )

        return {
            "success": True,
            "SessionID": data.SessionID,
            "OutputFile": output_path,
            "CloudinaryURL": upload_result["secure_url"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )