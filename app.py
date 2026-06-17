"""
Embedded Dev Tutorials - FastAPI Backend
v1.4.1
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI(title="Embedded Dev Tutorials", version="1.4.1")

# Static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def index():
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.4.1", "service": "embedded-dev-tutorials"}


@app.get("/tutorials/{page_name:path}")
async def tutorial_page(page_name: str):
    """SPA fallback: return index.html for any tutorial route"""
    return FileResponse(os.path.join(static_dir, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
