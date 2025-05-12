from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import os
import shutil
import subprocess
import logging

UPLOAD_DIR = "uploads"
SRT_DIR = "subtitles"

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SRT_DIR, exist_ok=True)

SUPPORTED_EXTENSIONS = {"mp4", "mkv", "mov", "mp3", "wav", "m4a"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in SUPPORTED_EXTENSIONS

import whisper
import threading
import time

# Global dicts for progress and partial transcript
progress_dict = {}
transcript_dict = {}

# Use Whisper Python API for real-time progress and transcript

def run_whisper(input_path, output_path, file_id):
    try:
        logging.info(f"[EVENT] Starting Whisper transcription for {input_path}")
        model = whisper.load_model("base")
        audio = whisper.load_audio(input_path)
        # Do NOT pad_or_trim here; process the full audio
        result = model.transcribe(audio, task="translate", verbose=False, language="en", word_timestamps=False, condition_on_previous_text=True, beam_size=5, best_of=5, fp16=False)
        # Simulate live progress and transcript updates after transcription completes
        transcript = ""
        segments = result.get("segments", [])
        total = len(segments)
        if total > 0:
            for idx, seg in enumerate(segments):
                transcript += seg["text"] + "\n"
                transcript_dict[file_id] = transcript
                progress_dict[file_id] = int(100 * (idx + 1) / total)
                time.sleep(0.15)  # simulate delay for frontend polling
        else:
            transcript_dict[file_id] = result.get("text", "")
            progress_dict[file_id] = 100
        # Write SRT file
        with open(output_path, "w", encoding="utf-8") as f:
            for idx, seg in enumerate(result["segments"], 1):
                f.write(f"{idx}\n{whisper.utils.format_timestamp(seg['start'])} --> {whisper.utils.format_timestamp(seg['end'])}\n{seg['text'].strip()}\n\n")
        logging.info(f"[EVENT] Whisper transcription completed for {input_path}")
        # Delete the uploaded file after transcription
        try:
            os.remove(input_path)
            logging.info(f"[CLEANUP] Deleted uploaded file: {input_path}")
        except Exception as cleanup_err:
            logging.warning(f"[CLEANUP] Failed to delete uploaded file: {input_path}. Error: {cleanup_err}")
        # Mark progress as 100 and transcript as final
        progress_dict[file_id] = 100
        transcript_dict[file_id] = transcript
    except Exception as e:
        logging.error(f"[ERROR] Whisper failed for {input_path}: {e}")
        progress_dict[file_id] = -1
        transcript_dict[file_id] = f"[ERROR] {e}"
        raise

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logging.info(f"[REQUEST] {request.method} {request.url}")
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logging.error(f"[ERROR] Unhandled exception: {e}")
        return JSONResponse(status_code=500, content={"detail": str(e)})

@app.post("/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        if not allowed_file(file.filename):
            logging.warning(f"[ERROR] Unsupported file type: {file.filename}")
            raise HTTPException(status_code=400, detail="Unsupported file type.")
        file_id = str(uuid.uuid4())
        ext = file.filename.rsplit(".", 1)[1].lower()
        input_path = os.path.join(UPLOAD_DIR, f"{file_id}.{ext}")
        output_path = os.path.join(SRT_DIR, f"{file_id}.srt")
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logging.info(f"[EVENT] Upload received: {input_path}")
        background_tasks.add_task(run_whisper, input_path, output_path, file_id)
        return {"file_id": file_id}
    except Exception as e:
        logging.error(f"[ERROR] Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/progress/{file_id}")
def progress_srt(file_id: str):
    progress = progress_dict.get(file_id, 0)
    transcript = transcript_dict.get(file_id, "")
    return {"progress": progress, "transcript": transcript}

@app.get("/download/{file_id}")
def download_srt(file_id: str):
    srt_path = os.path.join(SRT_DIR, f"{file_id}.srt")
    if not os.path.exists(srt_path):
        logging.info(f"[DOWNLOAD] SRT not ready for file_id {file_id}")
        raise HTTPException(status_code=404, detail="SRT not ready yet.")
    logging.info(f"[DOWNLOAD] SRT ready and served for file_id {file_id}")
    return FileResponse(srt_path, media_type="text/plain", filename=f"{file_id}.srt")

@app.get("/status/{file_id}")
def status_srt(file_id: str):
    srt_path = os.path.join(SRT_DIR, f"{file_id}.srt")
    if os.path.exists(srt_path):
        logging.info(f"[STATUS] SRT done for file_id {file_id}")
        return {"status": "done"}
    else:
        logging.info(f"[STATUS] SRT processing for file_id {file_id}")
        return {"status": "processing"}
