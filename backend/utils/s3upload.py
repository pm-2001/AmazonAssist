from fastapi import UploadFile
import os
from dotenv import load_dotenv
import boto3
load_dotenv()

BUCKET_NAME = os.getenv("BUCKET_NAME")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

def s3fileUpload(file_content:UploadFile,item_name:str):
    if file_content:
        s3.upload_fileobj(file_content,BUCKET_NAME,f"{item_name}.png")
        link = "https://d1voydi2q6xpb1.cloudfront.net/"f"{item_name}.png"
        return link
    else:
        return "error in uploading"