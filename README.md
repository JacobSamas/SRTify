# SRTify: Auto English Subtitles Generator

Generate accurate English subtitles (SRT files) for your audio and video files using OpenAI Whisper, FastAPI, and Next.js.

## Features
- Drag-and-drop or select audio/video files (MP4, MKV, MOV, WMV, AVI, FLV, WEBM, MP3, WAV, M4A, AAC, OGG, OPUS, TS, MTS, 3GP, M4V, MPEG, MPG, and more)
- FastAPI backend with Whisper for transcription
- Real-time status updates, animated progress bar, transcript preview, and download link for generated SRT
- Uploaded files are deleted after processing for privacy
- No user media is stored
- Modern, animated UI/UX: glassmorphism, 3D/hover effects, animated background, custom cursor, toast notifications, entrance/microinteractions

## How it Works
1. Upload a supported media file via the web interface
2. The backend transcribes it with Whisper and generates an SRT
3. Download the SRT as soon as it's ready

## Tech Stack
- **Frontend:** Next.js, Tailwind CSS
- **Backend:** FastAPI, OpenAI Whisper, FFmpeg

## Setup
1. Clone the repo
2. Install Python and Node.js dependencies
3. Start the FastAPI backend: `python3 -m uvicorn main:app --reload --port 8001`
4. Start the Next.js frontend:
   - With npm: `npm run dev` (from `frontend/`)
   - With pnpm: `pnpm dev` (from `frontend/`)
5. Set `NEXT_PUBLIC_BACKEND_URL` in your frontend `.env` if backend is not on default `http://localhost:8001`

## Supported Formats
- All major video/audio formats supported thanks to Whisper + ffmpeg: MP4, MKV, MOV, WMV, AVI, FLV, WEBM, MP3, WAV, M4A, AAC, OGG, OPUS, TS, MTS, 3GP, M4V, MPEG, MPG, and more.
- For rare formats, ensure ffmpeg is installed and available in your backend environment.

## Privacy
- Uploaded files are deleted immediately after transcription
- SRT files are generated and served for download, not stored long-term

## License
MIT
