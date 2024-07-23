from fastapi import FastAPI, APIRouter, Depends, status, File, UploadFile, HTTPException
from views.textdetect import textToDesc
from models.text_to_desc import textDescModel
from models.user import Users
from utils.JWTBearer import JWTBearer

router = APIRouter(prefix="/text")



@router.post("")
# async def image(file: UploadFile = File(...),db: Session = Depends(get_db),user: Users = Depends(JWTBearer())): 
async def text(request: textDescModel): 
    return textToDesc(request)