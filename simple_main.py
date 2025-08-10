from fastapi import FastAPI, UploadFile, File, HTTPException
import shutil
import os
from pathlib import Path
from datetime import datetime

app = FastAPI(title="Voice-to-Text Meeting Assistant", version="1.0.0")

# Ensure uploads directory exists
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_AUDIO_TYPES = {
    "audio/mpeg",       # .mp3
    "audio/mp4",        # .m4a
    "audio/m4a",        # .m4a (alternative MIME type)
    "audio/x-m4a",      # .m4a (another MIME type)
    "audio/wav",        # .wav
    "audio/x-wav",      # .wav
    "audio/aac",        # .aac
    "video/mp4"         # .mp4 (audio from video)
}

@app.get("/")
async def root():
    return {"message": "Voice-to-Text Meeting Assistant API"}


@app.post("/upload-recording/")
async def upload_recording(
    title: str,
    file: UploadFile = File(...)
):
    """Upload an audio/video file for transcription"""
    
    # Validate file type
    if file.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not supported. Supported types: {list(ALLOWED_AUDIO_TYPES)}"
        )
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = Path(file.filename).suffix
    unique_filename = f"{timestamp}_{file.filename}"
    file_path = UPLOAD_DIR / unique_filename
    
    try:
        # Save file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file info
        file_size = os.path.getsize(file_path)
        file_type = file_extension.lstrip('.')
        
        return {
            "message": "File uploaded successfully",
            "filename": file.filename,
            "unique_filename": unique_filename,
            "file_size": file_size,
            "file_type": file_type,
            "title": title
        }
        
    except Exception as e:
        # Clean up file if operation fails
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/files/")
async def list_uploaded_files():
    """List all uploaded files"""
    files = []
    for file_path in UPLOAD_DIR.glob("*"):
        if file_path.is_file():
            stat = file_path.stat()
            files.append({
                "filename": file_path.name,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
            })
    return {"files": files, "total": len(files)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
