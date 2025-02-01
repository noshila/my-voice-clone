from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
import os
import uuid
from io import BytesIO
import soundfile as sf
from .tts import clone_voice_tts
from .utils import convert_audio_to_wav, read_wav_from_bytes

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="frontend")

# Ensure static/generated_audio directory exists
os.makedirs("static/generated_audio", exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/clone_voice/")
async def create_upload_file(
    request: Request,
    target_text: str = Form(...),
    prompt_audio_file: UploadFile = File(...)
):
    if not target_text:
        return {"error": "Text input is required."}
    if not prompt_audio_file:
        return {"error": "Prompt audio file is required."}

    try:
        prompt_audio_content = await prompt_audio_file.read()
        input_audio_buffer = BytesIO(prompt_audio_content)

        # Convert uploaded audio to WAV 16kHz
        temp_wav_input_path = f"static/temp_audio_{uuid.uuid4()}.wav"
        wav_path = convert_audio_to_wav(input_audio_buffer, temp_wav_input_path)

        if not wav_path:
            return {"error": "Failed to convert audio to WAV."}

        waveform, sample_rate = clone_voice_tts(wav_path, target_text)
        os.remove(wav_path) # Clean up temp file

        if waveform is None:
            return {"error": "TTS generation failed."}

        output_filename = f"generated_{uuid.uuid4()}.wav"
        output_filepath = os.path.join("static", "generated_audio", output_filename)
        sf.write(output_filepath, waveform, sample_rate)

        return {"audio_url": request.url_for("static", path=f"generated_audio/{output_filename}")}

    except Exception as e:
        print(f"Error processing request: {e}")
        return {"error": "Internal server error."}


@app.get("/download_audio/{filename}")
async def download_audio(filename: str):
    """Download endpoint for generated audio files."""
    audio_path = os.path.join("static", "generated_audio", filename)
    if os.path.exists(audio_path):
        return FileResponse(audio_path, media_type="audio/wav", filename=filename)
    else:
        return {"error": "Audio file not found."}
