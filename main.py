from fastapi import FastAPI, UploadFile, File, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import shutil
import uuid
import subprocess
import platform
import database
import conversion
from typing import Optional

# Initialize DB
database.init_db()

app = FastAPI(title="Convertr API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
UPLOADS_DIR = os.path.join(PROJECT_ROOT, "uploads")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

os.makedirs(UPLOADS_DIR, exist_ok=True)

# Helper for format from extension
def get_format_from_ext(filename: str):
    ext = os.path.splitext(filename)[1].lower().replace(".", "")
    return ext

@app.get("/api/health")
def health():
    soffice = conversion.get_libreoffice_path()
    try:
        proc = subprocess.run([soffice, "--version"], capture_output=True, text=True)
        return {
            "status": "ok",
            "libreoffice": "ok",
            "path": soffice,
            "version": proc.stdout.strip()
        }
    except Exception as e:
        return {"status": "error", "libreoffice": "not found", "path": soffice, "error": str(e)}

@app.get("/api/formats")
def get_formats():
    return {"formats": conversion.FORMAT_MAP}

@app.post("/api/files")
async def upload_file(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{ext}"
    stored_path = os.path.join(UPLOADS_DIR, unique_filename)
    
    with open(stored_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    record = database.create_file_record({
        "filename": unique_filename,
        "original_name": file.filename,
        "stored_path": stored_path,
        "mime_type": file.content_type,
        "size": os.path.getsize(stored_path),
        "format": get_format_from_ext(file.filename)
    })
    return record

@app.get("/api/files")
def list_files(skip: int = 0, take: int = 50):
    return database.list_files(skip, take)

@app.get("/api/files/{file_id}")
def get_file(file_id: str):
    record = database.get_file_by_id(file_id)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    return record

@app.put("/api/files/{file_id}")
def rename_file(file_id: str, data: dict):
    new_name = data.get("filename")
    if not new_name:
        raise HTTPException(status_code=400, detail="filename is required")
    record = database.update_file_name(file_id, new_name)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    return record

@app.delete("/api/files/{file_id}")
def delete_file(file_id: str):
    record = database.get_file_by_id(file_id)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    
    if os.path.exists(record["stored_path"]):
        os.remove(record["stored_path"])
    
    database.delete_file_record(file_id)
    return {"status": "success"}

@app.post("/api/convert")
async def convert_api(data: dict):
    file_id = data.get("fileId")
    target_format = data.get("targetFormat")
    
    if not file_id or not target_format:
        raise HTTPException(status_code=400, detail="fileId and targetFormat are required")
    
    record = database.get_file_by_id(file_id)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    
    result = await conversion.convert_file(record, target_format)
    if not result["success"]:
        return JSONResponse(status_code=400, content={"error": result["error"]})
    
    return {"fileId": result["id"], "filename": result["filename"]}

@app.get("/api/download/{file_id}")
def download_file(file_id: str):
    record = database.get_file_by_id(file_id)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        record["stored_path"], 
        media_type=record["mime_type"], 
        filename=record["original_name"]
    )

# Static files
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {"message": "Frontend directory not found at " + FRONTEND_DIR}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)
