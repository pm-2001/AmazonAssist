from fastapi import FastAPI, APIRouter, Depends, status, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import requests
import json

import os
from pathlib import Path
from dotenv import load_dotenv

from g4f.client import Client 
from g4f.Provider.GeminiPro import GeminiPro 
from g4f.Provider.GeminiProChat import GeminiProChat
from database.dbconnect import get_db,Base
from sqlalchemy.orm import Session
from models.user import Users
import io
import time
import boto3
import speech_recognition as sr
from models.history import Historys
from utils.s3upload import s3fileUpload
router = APIRouter()
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")
huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

client = Client(provider=GeminiProChat,api_key=gemini_api_key)
clientimage = Client(provider=GeminiPro, api_key=gemini_api_key)

HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
headers = {"Authorization": f"Bearer {huggingface_api_key}",
           "language":'en',
        }
HUGGINGFACE_SPEECH_TO_TEXT_API_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3"




def convert_to_dict(json_data):
    dict_data = []
    for item_name, tags_str in json_data.items():
        tags = [tag.strip() for tag in tags_str.split(',')]
        dict_data.append({item_name: tags})
    return dict_data


def extract_json(input_string):
    try:
        parsed_json = json.loads(input_string)
        return parsed_json
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return None

def query(payload, max_retries=10, retry_delay=30):
    retries = 0
    while retries < max_retries:
        response = requests.post(HUGGINGFACE_API_URL, headers=headers, json=payload)
        if response.status_code == 503:
            wait_time = retry_delay * (2 ** retries)
            print(f"Model is currently loading. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            retries += 1
        elif response.status_code == 200:
            return response.content
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return None
    
    print(f"Failed after {max_retries} retries.")
    return None


# def generate_images_from_json(json_data,db:Session,user):
def generate_images_from_json(json_data):
    db_history = Historys()
    new_json = {}
    for item in json_data:
        if item: 
            tags = json_data[item]  
            prompt = f"{item}: {', '.join(tags)}"
            print(prompt)
            image_bytes = query({"inputs": prompt})
            
            if image_bytes:
                try:
                    # image_link = save_image(image_bytes, item)
                    image = io.BytesIO(image_bytes)
                    image_link = s3fileUpload(image,item)
                    print(image_link)

                    new_json[item] = {
                        "tags": ', '.join(tags),
                        "image_link": image_link
                    }
                    # #saving to database
                    # db_history.user_id = user.id
                    # db_history.item_name = item
                    # db_history.link = image_link
                    # db.add(db_history)
                    # db.commit()
                    # db.refresh(db_history)
                    # print("data saved to database")

                except IOError:
                    print(f"Error: Could not generate image for {item}")
                    new_json[item] = {
                        "tags": ', '.join(tags),
                        "image_link": "Error: Image could not be generated"
                    }
        else:
            print(f"Error: Invalid item format in json_data: {item}")
    
    return new_json