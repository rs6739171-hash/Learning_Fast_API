from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api import master_router
from .sessions import create_db_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_tables()
    yield


app = FastAPI(
    title="StockFlow Inventory & Seller Management",
    description="Full-featured API with OAuth2 JWT Auth, Redis Token Blacklisting, and Async PostgreSQL ORM",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(master_router.router)

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def serve_frontend():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Welcome to FastAPI Inventory API. Visit /docs for documentation."}
