# Voice-to-Text Meeting Assistant

A powerful FastAPI application with AI-powered transcription and summarization capabilities.

## Features

- **User Authentication**: Secure JWT-based authentication system
- **Audio Upload**: Support for multiple audio formats (.mp3, .m4a, .wav, .aac, .mp4)
- **AI Transcription**: Powered by AssemblyAI for accurate speech-to-text
- **Smart Summarization**: Automatic meeting summaries and key points extraction
- **Action Items**: AI-powered action item detection from conversations
- **Personal Data**: Users can only access their own recordings and summaries

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **AI Services**: AssemblyAI for transcription
- **Authentication**: JWT tokens with bcrypt password hashing
- **File Handling**: Background processing for large audio files

## API Endpoints

### Authentication
- `POST /register` - Register new user
- `POST /login` - Login and get JWT token
- `GET /me` - Get current user info

### Recordings
- `POST /upload-recording/` - Upload audio files
- `GET /recordings/` - List user's recordings
- `GET /recordings/{id}` - Get specific recording
- `DELETE /recordings/{id}` - Delete recording

### AI Processing
- `POST /recordings/{id}/process-now` - Process immediately (synchronous)
- `POST /recordings/{id}/process` - Process in background (asynchronous)
- `GET /recordings/{id}/status` - Check processing status
- `GET /recordings/{id}/summary` - Get AI-generated summary
- `GET /summaries/` - List all summaries

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**:
   ```bash
   python main.py
   ```

3. **Access API documentation**:
   - Open http://localhost:8000/docs

## Project Structure

```
├── main.py                 # Main FastAPI application
├── database.py            # Database configuration
├── auth.py                # Authentication utilities
├── transcription_service.py # AI transcription service
├── models/                # Database models
│   ├── __init__.py
│   ├── users.py
│   ├── recordings.py
│   └── summry.py
├── schemas/               # Pydantic schemas
│   ├── __init__.py
│   ├── users.py
│   ├── recordings.py
│   └── summaries.py
├── uploads/               # Uploaded audio files
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Environment Variables

Create a `.env` file with:
```
ASSEMBLYAI_API_KEY=your_assemblyai_api_key
SECRET_KEY=your_secret_key_for_jwt
```

## Usage

1. **Register** a new account
2. **Login** to get access token
3. **Upload** audio recordings
4. **Process** recordings to get transcripts and summaries
5. **View** action items and key points

## License

MIT License
