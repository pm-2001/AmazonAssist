from fastapi import FastAPI, APIRouter, Depends, status, File, UploadFile, HTTPException
from DTO.userRequest import AuthRequestDTO
from sqlalchemy.orm import Session
from database.dbconnect import get_db
from views.imagedetect import upload_image
from models.text_to_desc import textDescModel
from models.user import Users
from utils.JWTBearer import JWTBearer

router = APIRouter(prefix="/image")



@router.post("")
# async def image(file: UploadFile = File(...),db: Session = Depends(get_db),user: Users = Depends(JWTBearer())): 
async def image(file: UploadFile = File(...)): 
    return upload_image(file)