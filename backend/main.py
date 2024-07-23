from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from routes import imagedetect,textdetect,videodetect,user,ytvideodetect

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*']
    )
]
app = FastAPI(middleware=middleware)
app.include_router(imagedetect.router)
app.include_router(textdetect.router)
app.include_router(videodetect.router)
app.include_router(ytvideodetect.router)
app.include_router(user.router)

@app.get("/")
def server_started():
    return {"message": "Server started successfully"}