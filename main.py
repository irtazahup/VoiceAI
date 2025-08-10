from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import shutil
import os
import json
from pathlib import Path
from datetime import datetime, timedelta

from database import get_db, engine, Base
from models.users import User
from models.recordings import Recording
from models.summry import Summary
from schemas.users import UserCreate, UserLogin, UserResponse, Token
from schemas.recordings import RecordingResponse, RecordingList
from schemas.summaries import SummaryResponse
from transcription_service import TranscriptionService
from auth import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    verify_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# Create tables
Base.metadata.create_all(bind=engine)

# Tags metadata for API documentation
tags_metadata = [
    {
        "name": "General",
        "description": "General API information and health checks",
    },
    {
        "name": "Authentication",
        "description": "User registration, login, and authentication management",
    },
    {
        "name": "Recordings",
        "description": "Upload, manage, and retrieve audio recordings",
    },
    {
        "name": "Processing",
        "description": "Process recordings for transcription and AI analysis",
    },
    {
        "name": "Summaries",
        "description": "AI-generated summaries, action items, and key points",
    },
]

app = FastAPI(
    title="Voice-to-Text Meeting Assistant",
    version="1.0.0",
    description="A comprehensive AI-powered voice recording and transcription application with intelligent summarization",
    openapi_tags=tags_metadata
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Security
security = HTTPBearer()

# Initialize transcription service
transcription_service = TranscriptionService()

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

# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user"""
    token = credentials.credentials
    user_id = verify_token(token)
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

# Background task for processing transcription
def process_transcription(recording_id: int, file_path: str):
    """Background task to process audio transcription and create summary"""
    db = next(get_db())
    
    try:
        # Update recording status
        recording = db.query(Recording).filter(Recording.id == recording_id).first()
        if not recording:
            return
        
        recording.status = "processing"
        db.commit()
        
        # Transcribe audio
        result = transcription_service.transcribe_audio(file_path)
        
        # Update recording with transcript
        recording.transcript = result["transcript"]
        recording.duration = result.get("audio_duration", 0) / 1000  # Convert to seconds
        recording.status = "transcribed"
        db.commit()
        
        # Extract action items and key points
        action_items = transcription_service.extract_action_items(result["transcript"])
        key_points = transcription_service.extract_key_points(result["summary"], result["transcript"])
        
        # Create summary
        summary = Summary(
            title=f"Summary of {recording.title}",
            content=result["summary"],
            action_items=json.dumps(action_items),
            key_points=json.dumps(key_points),
            status="completed",
            recording_id=recording.id
        )
        
        db.add(summary)
        recording.status = "completed"
        db.commit()
        
    except Exception as e:
        # Update recording status to error
        recording = db.query(Recording).filter(Recording.id == recording_id).first()
        if recording:
            recording.status = "error"
            db.commit()
        print(f"Transcription error: {str(e)}")
    finally:
        db.close()

@app.get("/", tags=["General"])
async def root():
    """Welcome endpoint for the Voice-to-Text Meeting Assistant API"""
    return {"message": "Voice-to-Text Meeting Assistant API"}

# Authentication endpoints
@app.post("/register", response_model=UserResponse, tags=["Authentication"])
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    new_user = User(
        name=user.name,
        email=user.email,
        password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@app.post("/login", response_model=Token, tags=["Authentication"])
async def login(user: UserLogin, db: Session = Depends(get_db)):
    """Login user and return access token"""
    db_user = db.query(User).filter(User.email == user.email).first()
    
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(db_user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=UserResponse, tags=["Authentication"])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@app.post("/upload-recording/", tags=["Recordings"])
async def upload_recording(
    title: str = Form(...),
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload an audio/video file for transcription (authenticated users only)"""
    
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
        
        # Create database record
        recording = Recording(
            title=title,
            filename=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            file_type=file_type,
            status="uploaded",
            user_id=current_user.id
        )
        
        db.add(recording)
        db.commit()
        db.refresh(recording)
        
        # Note: Auto-processing disabled to save AssemblyAI credits
        # Use POST /recordings/{id}/process or /recordings/{id}/process-now to start processing
        
        return {
            "message": "File uploaded successfully. Use /recordings/{}/process-now to transcribe.".format(recording.id),
            "recording_id": recording.id,
            "filename": recording.filename,
            "file_size": recording.file_size,
            "status": recording.status,
            "title": recording.title,
            "next_step": f"POST /recordings/{recording.id}/process-now"
        }
        
    except Exception as e:
        # Clean up file if database operation fails
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/recordings/", response_model=RecordingList, tags=["Recordings"])
async def get_my_recordings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all recordings for the authenticated user"""
    recordings = db.query(Recording).filter(Recording.user_id == current_user.id).all()
    return {"recordings": recordings, "total": len(recordings)}

@app.get("/recordings/{recording_id}", response_model=RecordingResponse, tags=["Recordings"])
async def get_recording(
    recording_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific recording (only if it belongs to the user)"""
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.user_id == current_user.id
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    return recording

@app.delete("/recordings/{recording_id}", tags=["Recordings"])
async def delete_recording(
    recording_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a recording (only if it belongs to the user)"""
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.user_id == current_user.id
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    # Delete file from disk
    if os.path.exists(recording.file_path):
        os.remove(recording.file_path)
    
    # Delete from database
    db.delete(recording)
    db.commit()
    
    return {"message": "Recording deleted successfully"}

# Processing endpoints
@app.post("/recordings/{recording_id}/process", tags=["Processing"])
async def process_recording_manually(
    recording_id: int,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger processing for a recording"""
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.user_id == current_user.id
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    if recording.status in ["processing", "completed"]:
        return {"message": f"Recording is already {recording.status}"}
    
    # Add background task for transcription
    background_tasks.add_task(process_transcription, recording.id, recording.file_path)
    
    return {"message": "Processing started", "recording_id": recording.id, "status": "processing"}

@app.get("/recordings/{recording_id}/status", tags=["Processing"])
async def get_processing_status(
    recording_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get processing status of a recording"""
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.user_id == current_user.id
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    result = {
        "recording_id": recording.id,
        "status": recording.status,
        "has_transcript": bool(recording.transcript),
        "has_summary": bool(recording.summary_obj),
        "duration": recording.duration
    }
    
    if recording.summary_obj:
        result["summary_status"] = recording.summary_obj.status
    
    return result

@app.get("/recordings/{recording_id}/summary", response_model=SummaryResponse, tags=["Summaries"])
async def get_recording_summary(
    recording_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get summary for a specific recording (only if it belongs to the user)"""
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.user_id == current_user.id
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    if not recording.summary_obj:
        return {
            "message": "Summary not available yet", 
            "status": recording.status,
            "suggestion": f"Use POST /recordings/{recording_id}/process to start processing"
        }
    
    return recording.summary_obj

@app.get("/summaries/", tags=["Summaries"])
async def get_my_summaries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all summaries for the authenticated user's recordings"""
    summaries = db.query(Summary).join(Recording).filter(
        Recording.user_id == current_user.id
    ).all()
    
    return {"summaries": summaries, "total": len(summaries)}

@app.post("/recordings/{recording_id}/process-now", tags=["Processing"])
async def process_recording_now(
    recording_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process recording immediately and return results (synchronous)"""
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.user_id == current_user.id
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    if recording.status == "completed":
        return {
            "message": "Recording already processed",
            "transcript": recording.transcript,
            "summary": recording.summary.content if recording.summary else None
        }
    
    try:
        # Update recording status
        recording.status = "processing"
        db.commit()
        
        # Process transcription
        result = transcription_service.transcribe_audio(recording.file_path)
        
        # Update recording with transcript
        recording.transcript = result["transcript"]
        recording.duration = result.get("audio_duration", 0) / 1000  # Convert to seconds
        recording.status = "transcribed"
        db.commit()
        
        # Extract action items and key points
        action_items = transcription_service.extract_action_items(result["transcript"])
        key_points = transcription_service.extract_key_points(result["summary"], result["transcript"])
        
        # Create or update summary
        existing_summary = db.query(Summary).filter(Summary.recording_id == recording.id).first()
        
        if existing_summary:
            existing_summary.content = result["summary"]
            existing_summary.action_items = json.dumps(action_items)
            existing_summary.key_points = json.dumps(key_points)
            existing_summary.status = "completed"
            summary = existing_summary
        else:
            summary = Summary(
                title=f"Summary of {recording.title}",
                content=result["summary"],
                action_items=json.dumps(action_items),
                key_points=json.dumps(key_points),
                status="completed",
                recording_id=recording.id
            )
            db.add(summary)
        
        recording.status = "completed"
        db.commit()
        db.refresh(summary)
        
        return {
            "message": "Processing completed successfully",
            "recording_id": recording.id,
            "transcript": recording.transcript,
            "summary": {
                "content": summary.content,
                "action_items": json.loads(summary.action_items) if summary.action_items else [],
                "key_points": json.loads(summary.key_points) if summary.key_points else []
            },
            "duration": recording.duration,
            "status": recording.status
        }
        
    except Exception as e:
        recording.status = "error"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
