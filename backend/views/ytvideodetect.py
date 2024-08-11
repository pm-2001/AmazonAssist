from fastapi import FastAPI, APIRouter, Depends, status, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import requests
import os
from pathlib import Path
from models.text_to_desc import textDescModel
from g4f.client import Client 
from g4f.Provider.GeminiPro import GeminiPro 
from g4f.Provider.GeminiProChat import GeminiProChat
from database.dbconnect import get_db,Base
from sqlalchemy.orm import Session
from models.user import Users
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
import yt_dlp
from database.config import GEMINI_API_KEY,HUUGINGFACE_API_KEY,HUGGINGFACE_SPEECH_TO_TEXT_API_URL
from utils.imagegen import extract_json,generate_images_from_json

client = Client(provider=GeminiProChat,api_key=GEMINI_API_KEY)
clientimage = Client(provider=GeminiPro, api_key=GEMINI_API_KEY)

headers = {"Authorization": f"Bearer {HUUGINGFACE_API_KEY}",
           "language":'en',
        }
    
def download_audio(url: str, output_path: str) -> str:
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path + '.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
            'preferredquality': '192',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return f"{output_path}.m4a"


def ytquery(filename: str):
    max_retries = 5
    retry_count = 0
    retry_delay = 100  # seconds
    while retry_count < max_retries:
        with open(filename, "rb") as f:
            data = f.read()
        response = requests.post(HUGGINGFACE_SPEECH_TO_TEXT_API_URL, headers=headers, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            response_data = response.json()
            if "error" in response_data:
                if "currently loading" in response_data["error"]:
                    estimated_time = response_data.get("estimated_time", retry_delay)
                    print(f"Model is loading. Retrying in {estimated_time} seconds...")
                    time.sleep(estimated_time)
                    retry_count += 1
                else:
                    print(f"Error from API: {response_data['error']}")
                    raise HTTPException(status_code=400, detail=response_data['error'])
            else:
                response.raise_for_status()
    raise Exception("Failed to get a response after multiple retries.")


def split_audio_to_chunks(audio, chunk_length_ms: int = 30000):
    duration_ms = len(audio)
    chunks = []
    for start in range(0, duration_ms, chunk_length_ms):
        end = min(start + chunk_length_ms, duration_ms)
        chunk = audio[start:end]
        chunks.append(chunk)
    return chunks


def export_audio_chunk_to_wav(chunk, filename: str):
    # Export the chunk to WAV format
    chunk.export(filename, format="wav")
    return filename


def process_audio_chunks(filename: str, chunk_length_ms: int = 30000):
    audio = AudioSegment.from_file(filename)
    chunks = split_audio_to_chunks(audio, chunk_length_ms)
    results = []
    for i, chunk in enumerate(chunks):
        chunk_filename = f"{filename}_{i}.wav"
        wav_chunk_filename = export_audio_chunk_to_wav(chunk, chunk_filename)
        result = ytquery(wav_chunk_filename)
        results.append(result)
        os.remove(wav_chunk_filename)  # Clean up chunk file
    return results

def youtube_video(request: dict):
    if 'url' not in request:
        raise HTTPException(status_code=400, detail="URL is missing in the request")

    video_url = request['url']
    output_filename = "downloaded_audio"

    try:
        final_output_filename = download_audio(video_url, output_filename)
        results = process_audio_chunks(final_output_filename)
        os.remove(final_output_filename)  # Clean up the downloaded file
        combined_result = "\n".join([result["text"] for result in results])
        ntpi= '; extract keywords related to each object described here and list them like this: {"Product name 1": ["feature 1","Feature 2","feature 3"],"Product name 2": ["feature 1","Feature 2","feature 3"],"Product name 3": ["feature 1","Feature 2","feature 3"],}'
        prompt = combined_result+ ntpi
        response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        )
        if response.choices[0].message.content:
            response_json = response.choices[0].message.content
            print(response_json)
            response_json = extract_json(response_json)
            if response_json:
                newjson = generate_images_from_json(response_json)
                print(newjson)
                return newjson  # Using the default Status code i.e. Status 200
            else:
                msg = [{"message": "Incorrect data/missing data"}]
                return JSONResponse(content=jsonable_encoder(msg), status_code=status.HTTP_404_NOT_FOUND)
        else:
            return f"Error: {response.status_code}, {response.text}"
        
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
