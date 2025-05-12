"use client";
import React, { useRef, useState } from "react";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8001";

export default function Home() {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [fileId, setFileId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [polling, setPolling] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [transcript, setTranscript] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
    else if (e.type === "dragleave") setDragActive(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setError("");
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError("");
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setProgress(0);
    setError("");
    setFileId(null);
    setPolling(false);
    setProcessing(false);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`${BACKEND_URL}/upload`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error("Upload failed");
      const data = await res.json();
      setFileId(data.file_id);
      setPolling(true);
      setProcessing(true);
    } catch (e) {
      setError("Upload or processing failed. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  // Poll for SRT progress and transcript
  React.useEffect(() => {
    if (fileId && polling) {
      let attempts = 0;
      const interval = setInterval(async () => {
        attempts++;
        if (attempts > 120) { // 10 minutes
          setError("Processing is taking too long. Please try again later.");
          setProcessing(false);
          clearInterval(interval);
          setPolling(false);
          return;
        }
        try {
          const res = await fetch(`${BACKEND_URL}/progress/${fileId}`);
          if (res.ok) {
            const data = await res.json();
            setProgress(data.progress || 0);
            setTranscript(data.transcript || "");
            if (data.progress >= 100) {
              setPolling(false);
              setProcessing(false);
              clearInterval(interval);
            }
          }
        } catch (err) {
          console.error("[DEBUG] Progress polling error:", err);
          // network or server error, treat as processing
        }
      }, 1500); // 1.5 seconds for smoother updates
      return () => {
        clearInterval(interval);
        setProcessing(false);
      };
    }
  }, [fileId, polling]);

  return (
    <div className="flex flex-col items-center min-h-screen justify-center bg-gray-50 dark:bg-black p-4">
      <h1 className="text-3xl font-bold mb-8 text-center">SRTify: Auto English Subtitles Generator</h1>
      <div
        className={`w-full max-w-lg p-8 border-2 border-dashed rounded-xl bg-white dark:bg-zinc-900 transition-colors ${dragActive ? "border-blue-500 bg-blue-50 dark:bg-zinc-800" : "border-gray-300"}`}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        style={{ cursor: "pointer" }}
      >
        <input
          type="file"
          accept=".mp4,.mkv,.mov,.mp3,.wav,.m4a"
          className="hidden"
          ref={inputRef}
          onChange={handleChange}
        />
        <div className="flex flex-col items-center justify-center gap-2">
          <span className="text-gray-700 dark:text-gray-200 text-lg font-medium">
            Drag & drop a video/audio file here
          </span>
          <span className="text-gray-500 text-sm">or click to select</span>
          <span className="text-xs text-gray-400 mt-2">
            Supported: MP4, MKV, MOV, MP3, WAV, M4A
          </span>
        </div>
        {file && (
          <div className="mt-4 text-center text-sm text-blue-700 dark:text-blue-300">
            Selected: {file.name}
          </div>
        )}
      </div>
      {processing && (
        <div className="text-blue-500 mt-2">Processing your file... This may take a few minutes for large uploads.</div>
      )}
      {error && <div className="text-red-500 mt-2">{error}</div>}
      <button
        className="mt-6 px-6 py-2 rounded bg-blue-600 text-white font-semibold hover:bg-blue-700 disabled:opacity-50"
        onClick={handleUpload}
        disabled={!file || uploading || polling}
      >
        {uploading ? "Uploading..." : polling ? "Processing..." : "Upload & Generate SRT"}
      </button>
      {(uploading || polling) && (
        <div className="mt-4 w-full max-w-lg">
          <div className="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700 overflow-hidden">
            {/* Indeterminate bar animation */}
            <div className={`bg-blue-600 h-2.5 rounded-full animate-indeterminate`}
                style={{ width: uploading ? '100%' : '40%' }}></div>
          </div>
          <style jsx>{`
            @keyframes indeterminate {
              0% { margin-left: -40%; width: 40%; }
              100% { margin-left: 100%; width: 40%; }
            }
            .animate-indeterminate {
              animation: indeterminate 1.2s infinite linear;
            }
          `}</style>
          <div className="text-center text-xs mt-2 text-gray-500">
            {uploading ? "Uploading..." : `Generating subtitles...`}
          </div>
        </div>
      )}
      {fileId && !polling && (
        <div className="mt-4 w-full max-w-lg">
          <div className="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700">
            <div
              className="bg-blue-600 h-2.5 rounded-full transition-all"
              style={{ width: `100%` }}
            ></div>
          </div>
          <div className="text-center text-xs mt-2 text-gray-500">
            Done!
          </div>
        </div>
      )}
      {fileId && !polling && transcript && (
        <div className="bg-gray-50 dark:bg-zinc-800 rounded p-3 mt-8 text-xs max-h-60 overflow-y-auto border border-gray-200 dark:border-zinc-700 w-full max-w-lg">
          <div className="font-semibold mb-2 text-blue-600 dark:text-blue-300">Transcript Preview:</div>
          {transcript.split("\n").map((line, i) => line.trim() && <div key={i}>{line}</div>)}
        </div>
      )}
      {fileId && !polling && (
        <a
          className="mt-8 px-6 py-2 rounded bg-green-600 text-white font-semibold hover:bg-green-700"
          href={`${BACKEND_URL}/download/${fileId}`}
          download={`subtitles-${fileId}.srt`}
        >
          Download SRT File
        </a>
      )}
      <footer className="mt-16 text-gray-400 text-xs text-center">
        No media is stored. Files are processed and deleted automatically.<br />
        Built with Next.js, FastAPI, and Whisper.
      </footer>
    </div>
  );
}
