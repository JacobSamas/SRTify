# SRTify Backend

FastAPI app for handling uploads, running Whisper, and serving SRT files.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the server:
   ```bash
   uvicorn main:app --reload
   ```
3. Requires Whisper CLI and FFmpeg installed.
