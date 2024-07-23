from fastapi import FastAPI, APIRouter, Depends, status, File
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import os
from pathlib import Path

from models.text_to_desc import textDescModel
from g4f.client import Client 
from g4f.Provider.GeminiPro import GeminiPro 
from g4f.Provider.GeminiProChat import GeminiProChat
from database.dbconnect import get_db
from sqlalchemy.orm import Session
from models.user import Users
from fastapi.encoders import jsonable_encoder
from utils.imagegen import extract_json,generate_images_from_json
from database.config import GEMINI_API_KEY

client = Client(provider=GeminiProChat,api_key=GEMINI_API_KEY)

# def textToDesc(request: textDescModel,db: Session = Depends(get_db),user: Users = Depends(JWTBearer())):
def textToDesc(request: textDescModel):
    print(request.text)
    if request.text:
        ntpi= '; extract keywords related to each object described here and list them like this: {"Product name 1": ["feature 1","Feature 2","feature 3"],"Product name 2": ["feature 1","Feature 2","feature 3"],"Product name 3": ["feature 1","Feature 2","feature 3"],}'
        prompt = request.text + ntpi
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )

        if response.choices[0].message.content:
            response_json = response.choices[0].message.content
            response_json = extract_json(response_json)
            if response_json:
                # newjson = generate_images_from_json(response_json,db,user)
                newjson = generate_images_from_json(response_json)
                print(newjson)
                return newjson  # Using the default Status code i.e. Status 200
            else:
                msg = [{"message": "Incorrect data/missing data"}]
                return JSONResponse(content=jsonable_encoder(msg), status_code=status.HTTP_404_NOT_FOUND)
        else:
            return f"Error: {response.status_code}, {response.text}"
    else:
        msg = [{"message": "Incorrect data/missing data"}]
        return JSONResponse(content=jsonable_encoder(msg), status_code=status.HTTP_404_NOT_FOUND)