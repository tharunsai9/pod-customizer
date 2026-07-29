from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import traceback
import requests
import fitz
from PIL import Image

import cloudinary
import cloudinary.uploader

# -------------------------------------------------
# Configure Cloudinary
# -------------------------------------------------

cloudinary.config(
    cloudinary_url=os.environ["CLOUDINARY_URL"]
)

# -------------------------------------------------
# FastAPI
# -------------------------------------------------

app = FastAPI()

TEMP_FOLDER = "temp"
OUTPUT_FOLDER = "output"

os.makedirs(TEMP_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# -------------------------------------------------
# Request Model
# -------------------------------------------------

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


@app.get("/")
def root():
    return {
        "status": "running"
    }


@app.post("/customize")
def customize(data: PODRequest):

    try:

        print("===================================")
        print("Request received")
        print(data)

        filename = f"{data.FileName}.{data.FileType}"
        temp_path = os.path.join(TEMP_FOLDER, filename)

        print("Downloading file...")
        response = requests.get(data.FileURL, timeout=60)
        response.raise_for_status()

        with open(temp_path, "wb") as f:
            f.write(response.content)

        print("Downloaded:", temp_path)

        # ----------------------------------------
        # PDF
        # ----------------------------------------

        if data.FileType.lower() == "pdf":

            print("Processing PDF...")

            doc = fitz.open(temp_path)

            output_path = os.path.join(
                OUTPUT_FOLDER,
                f"{data.SessionID}.pdf"
            )

            doc.save(output_path)
            doc.close()

            print("Uploading PDF to Cloudinary...")

            upload_result = cloudinary.uploader.upload(
                output_path,
                folder="POD_Output",
                resource_type="image"
            )

        # ----------------------------------------
        # IMAGE
        # ----------------------------------------

        else:

            print("Processing Image...")

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

            print("Uploading Image to Cloudinary...")

            upload_result = cloudinary.uploader.upload(
                output_path,
                folder="POD_Output"
            )

        print("Upload Success")
        print(upload_result)

        return {
            "success": True,
            "SessionID": data.SessionID,
            "OutputFile": output_path,
            "CloudinaryURL": upload_result["secure_url"]
        }

    except Exception as e:

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )