from pydub import AudioSegment
import soundfile as sf
import io

def convert_audio_to_wav(input_file, output_file, target_sr=16000):
    """
    Converts an audio file to WAV format with a specified sample rate.

    Args:
        input_file (BytesIO): Input audio file as bytes.
        output_file (str): Path to save the output WAV file.
        target_sr (int): Target sample rate (default 16000 Hz).
    """
    try:
        audio = AudioSegment.from_file(input_file)
        audio = audio.set_frame_rate(target_sr)
        audio.export(output_file, format="wav")
        return output_file
    except Exception as e:
        print(f"Error during audio conversion: {e}")
        return None

def read_wav_from_bytes(audio_bytes, target_sr=16000):
    """Reads WAV audio data from bytes and resamples if necessary."""
    try:
        with io.BytesIO(audio_bytes) as wav_io:
            audio, sr = sf.read(wav_io)
            if sr != target_sr:
                print(f"Warning: Input audio sample rate is {sr} Hz, resampling to {target_sr} Hz.")
                audio = AudioSegment.from_bytes(audio.tobytes(), frame_rate=sr, sample_width=audio.dtype.itemsize, channels=1) # Assuming mono
                audio = audio.set_frame_rate(target_sr)
                wav_bytes = io.BytesIO()
                audio.export(wav_bytes, format="wav")
                wav_bytes.seek(0)
                audio, sr = sf.read(wav_bytes) # Read again with resampled data
            return audio, target_sr
    except Exception as e:
        print(f"Error reading WAV from bytes: {e}")
        return None, None
