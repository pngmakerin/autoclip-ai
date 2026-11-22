import os, uuid, shutil, subprocess
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).parent
WORK = ROOT / "work"
WORK.mkdir(exist_ok=True)

app = FastAPI(title="AutoClip AI")
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
        raise HTTPException(400, "Duration must be 30 or 60 seconds")
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
            # yt-dlp can only download videos the user is authorized to access.
            subprocess.run(
                ["yt-dlp", "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
                 "--merge-output-format", "mp4", "-o", str(source), video_url],
                check=True, timeout=900
            )
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(source)],
            capture_output=True, text=True, check=True
        )
        total = float(probe.stdout.strip())
        if total < duration:
            raise HTTPException(400, f"Video must be at least {duration} seconds long")
        # Starter version: creates a sample clip from the beginning.
        # AI highlight detection and speech captions are the next development stage.
        output = job / "clip.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-ss", "0", "-i", str(source), "-t", str(duration),
             "-vf", "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
             "-c:a", "aac", "-movflags", "+faststart", str(output)],
            check=True, timeout=900
        )
        return FileResponse(output, media_type="video/mp4",
                            filename="autoclip.mp4",
                            background=None)
    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "Processing timed out. Try a shorter/smaller video.")
    except Exception as exc:
        raise HTTPException(500, f"Could not process video: {str(exc)[:250]}")
