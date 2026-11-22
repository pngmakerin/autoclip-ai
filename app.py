
import os
import uuid
import shutil
import subprocess
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).parent
WORK = ROOT / "work"
WORK.mkdir(exist_ok=True)

app = FastAPI(title="AutoClip AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/")
def home():
    return FileResponse(ROOT / "static" / "index.html")


@app.post("/api/process")
async def process_video(
    video: UploadFile = File(None),
    video_url: str = Form(""),
    duration: int = Form(30),
    language: str = Form("hi")
):
    if duration not in (30, 60):
        raise HTTPException(400, "Invalid duration")

    if not video and not video_url.strip():
        raise HTTPException(400, "Upload a video or enter a URL")

    job = WORK / str(uuid.uuid4())
    job.mkdir()
    source = job / "source.mp4"

    try:
        if video:
            with source.open("wb") as out:
                shutil.copyfileobj(video.file, out)
        else:
            subprocess.run(
                [
                    "yt-dlp", "-f",
                    "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
                    "--merge-output-format", "mp4",
                    "-o", str(source), video_url
                ],
                check=True,
                timeout=900
            )

        probe = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(source)
            ],
            capture_output=True,
            text=True,
            check=True
        )

        total = float(probe.stdout.strip())

        if total < duration:
            raise HTTPException(
                400, f"Video must be at least {duration} seconds"
            )

        output = job / "clip.mp4"

        subprocess.run(
            [
                "ffmpeg", "-y", "-ss", "0", "-i", str(source),
                "-t", str(duration),
                "-vf",
                "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280",
                "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "23", "-c:a", "aac",
                "-movflags", "+faststart", str(output)
            ],
            check=True,
            timeout=900
        )

        return FileResponse(
            output,
            media_type="video/mp4",
            filename="autoclip.mp4"
        )

    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "Processing timed out")
    except Exception as exc:
        raise HTTPException(500, str(exc)[:250])

