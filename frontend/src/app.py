from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from routes.home import router as home_router
from routes.dashboard import router as dashboard_router
from routes.chatbot import router as chatbot_router
from routes.api import router as api_router

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

templates = Jinja2Templates(directory= BASE_DIR / "templates")

app.mount("/static", StaticFiles(directory= BASE_DIR / "static"), name="static")

# Make templates available to routers
app.state.templates = templates

app.include_router(home_router)
app.include_router(dashboard_router)
app.include_router(chatbot_router)
app.include_router(api_router)