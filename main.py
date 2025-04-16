from contextlib import asynccontextmanager
from typing import Optional
from databases import Database
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import urls  # Ensure this is defined correctly
from database_manager import DatabaseManager
import os
from supabase import create_client, Client

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")
database = Database(DATABASE_URL)
dbm = DatabaseManager(database, urls)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()

app = FastAPI(lifespan=lifespan)

# Static files setup for frontend
app.mount("/static", StaticFiles(directory="static", html=True), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production environments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class URLRequest(BaseModel):
    original_url: str
    custom_short: Optional[str] = None

BASE_URL = os.getenv("BASE_URL")

# Route to serve homepage
@app.get("/")
async def serve_homepage():
    return FileResponse("static/index.html")

# Route to shorten URLs
@app.post("/shorten")
async def shorten_url(request: URLRequest):
    try:
        short_id = await dbm.add_url(request.original_url, request.custom_short)
        short_url = f"{BASE_URL}/{short_id}"

        # Fetch the QR code URL from the database
        result = await dbm.get_url(short_id)  
        qr_url = result.qr_code  

        return {
            "original_url": request.original_url,
            "short_url": short_url,
            "qr_code_url": qr_url  # Supabase URL from the database
        }
    except Exception as e:
        return {"error": str(e)}

# Route to redirect to long URL
@app.get("/{short_url}")
async def redirect_to_long_url(short_url: str):
    try:
        long_url = await dbm.get_url(short_url)
        if long_url:
            return RedirectResponse(url=long_url)
        return {"error": "Short URL not found"}
    except Exception as e:
        return {"error": str(e)}