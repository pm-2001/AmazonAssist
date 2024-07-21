from fastapi import FastAPI, APIRouter, Depends, status, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import shutil
import re
import os
from pathlib import Path
from dotenv import load_dotenv
from models.text_to_desc import textDescModel
from g4f.client import Client 
from g4f.Provider.GeminiPro import GeminiPro 
from g4f.Provider.GeminiProChat import GeminiProChat
from database.dbconnect import get_db,Base
from sqlalchemy.orm import Session
from models.user import Users
from PIL import Image
import io
from fastapi.encoders import jsonable_encoder
import time
from g4f.Provider.FreeChatgpt import FreeChatgpt
import boto3
import tempfile
import moviepy.editor as mp
import speech_recognition as sr
from models.history import Historys
from pydub import AudioSegment
from utils.imagegen import extract_json,generate_images_from_json
router = APIRouter()
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

# Initialize the client with the GeminiPro provider
client = Client(provider=GeminiProChat,api_key=gemini_api_key)
clientimage = Client(provider=GeminiPro, api_key=gemini_api_key)

# Prompts
set_lang_english = "Reply only in English; "


def upload_image(file: UploadFile = File(...)):
    try:
        upload_folder = Path("uploaded_images")
        upload_folder.mkdir(exist_ok=True)
        file_path = upload_folder / file.filename

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
       
        # Use the image with g4f.client
        with file_path.open("rb") as img:
            # ntpi= '; find name of products in image and list product name and features like this json list : "{"Product name 1": ["feature 1","Feature 2","feature 3"],"Product name 2": ["feature 1","Feature 2","feature 3"],"Product name 3": ["feature 1","Feature 2","feature 3"],};without ``` '
            ntpi1= '; only return name of product;without ``` '
            # prompt = set_lang_english+ntpi+image_identify_prompt_instructions2
            response = clientimage.chat.completions.create(
                model="gemini-pro-vision",
                messages=[{"role": "user", "content": ntpi1}],
                image=img
            )
        # Extract the response content
        response_content = response.choices[0].message.content
        print(response_content)
        # Delete the locally saved image
        file_path.unlink()

        ntpi2= '; for the products given ,list product names as key and features as value in given prompt like this: {"Product name 1": ["feature 1","Feature 2","feature 3"],"Product name 2": ["feature 1","Feature 2","feature 3"],"Product name 3": ["feature 1","Feature 2","feature 3"],}; without ```'
        prompt = set_lang_english+ response_content+ntpi2
        response1 = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )

        if response1.choices[0].message.content:
            response_json = response1.choices[0].message.content
            print(response_json)
            response_json = extract_json(response_json)
            if response_json:
                new_json = generate_images_from_json(response_json)
                return new_json 
            else:
                msg = [{"message": "Incorrect data/missing data"}]
                return JSONResponse(content=jsonable_encoder(msg), status_code=status.HTTP_400_BAD_REQUEST)
        else:
            return f"Error: {response.status_code}, {response.text}"

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)