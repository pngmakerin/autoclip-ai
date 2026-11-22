# AutoClip AI — starter backend

This starter backend accepts an uploaded video or a permitted public video URL and exports a 9:16 sample clip.

## Important limitations
- This is a **starter**, not the complete AI viral-moment product yet.
- It currently cuts a sample from the beginning; it does not detect viral moments or create Hindi/English captions.
- Free hosting may sleep, limit processing time, or run out of memory/storage.
- Only process videos you own or have permission to use. Do not use it to bypass DRM, paywalls, or access controls.

## Run locally
1. Install Python 3.10+ and FFmpeg.
2. Run `pip install -r requirements.txt`.
3. Run `uvicorn app:app --host 0.0.0.0 --port 8000`.
4. Open `http://localhost:8000`.

## Deploy
The included `render.yaml` is a starting point for Render. Push this project to a GitHub repository, then create a Render web service from that repository. Review Render's current free-plan limits before deploying.
