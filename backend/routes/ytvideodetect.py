from fastapi import FastAPI, APIRouter, Depends, status, File, UploadFile, HTTPException
from DTO.userRequest import AuthRequestDTO
from sqlalchemy.orm import Session
from database.dbconnect import get_db
from views.ytvideodetect import youtube_video
from models.user import Users
from utils.JWTBearer import JWTBearer

router = APIRouter(prefix="/video")

@router.post("")
# async def video(request: textDescModel,db: Session = Depends(get_db),user: Users = Depends(JWTBearer())):
async def ytvideo(file: UploadFile = File(...)):
    return youtube_video(file)