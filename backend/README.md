# SRTify Backend

FastAPI app for handling uploads, running Whisper, and serving SRT files.

## Supported Formats
- Accepts all major audio/video formats: MP4, MKV, MOV, WMV, AVI, FLV, WEBM, MP3, WAV, M4A, AAC, OGG, OPUS, TS, MTS, 3GP, M4V, MPEG, MPG, and more.
- Requires Whisper + ffmpeg for full format support.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the server:
   ```bash
   uvicorn main:app --reload
   ```
3. Requires Whisper and FFmpeg installed.

## Privacy
- Uploaded files are deleted after processing.
- No user media is stored long-term.
