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

def run_whisper(input_path, output_path):
    try:
        logging.info(f"[EVENT] Starting Whisper transcription for {input_path}")
        cmd = [
            "whisper",
            input_path,
            "--task", "translate",
            "--output_format", "srt",
            "--output_dir", os.path.dirname(output_path),
        ]
        subprocess.run(cmd, check=True)
        srt_dir = os.path.dirname(output_path)
        logging.info(f"[DEBUG] Files in SRT_DIR after Whisper: {os.listdir(srt_dir)}")
        base = os.path.splitext(os.path.basename(input_path))[0]
        generated = os.path.join(srt_dir, f"{base}.srt")
        if os.path.exists(generated):
            if generated != output_path:
                logging.info(f"[DEBUG] Renaming {generated} to {output_path}")
                os.rename(generated, output_path)
        elif os.path.exists(output_path):
            logging.info(f"[DEBUG] SRT already at expected location: {output_path}")
        else:
            srt_files = [f for f in os.listdir(srt_dir) if f.endswith('.srt')]
            if srt_files:
                found = os.path.join(srt_dir, srt_files[0])
                logging.info(f"[DEBUG] Renaming found SRT {found} to {output_path}")
                os.rename(found, output_path)
            else:
                logging.error(f"[ERROR] No SRT found in {srt_dir}")
                raise Exception("SRT file not generated.")
        logging.info(f"[EVENT] Whisper transcription completed for {input_path}")
        # Delete the uploaded file after transcription
        try:
            os.remove(input_path)
            logging.info(f"[CLEANUP] Deleted uploaded file: {input_path}")
        except Exception as cleanup_err:
            logging.warning(f"[CLEANUP] Failed to delete uploaded file: {input_path}. Error: {cleanup_err}")
    except Exception as e:
        logging.error(f"[ERROR] Whisper failed for {input_path}: {e}")
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
        background_tasks.add_task(run_whisper, input_path, output_path)
        return {"file_id": file_id}
    except Exception as e:
        logging.error(f"[ERROR] Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


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
