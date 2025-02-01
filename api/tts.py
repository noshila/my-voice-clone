from transformers import AutoTokenizer, AutoModelForCausalLM
from xcodec2.modeling_xcodec2 import XCodec2Model
import soundfile as sf
import torch
import os
from dotenv import load_dotenv

load_dotenv()
HF_TOKEN = os.getenv("hf_jmansoor1347")
# Model paths - adjust if you place models in different locations
LLASA_MODEL_NAME = 'HKUST-Audio/Llasa-1B'
XCODEC2_MODEL_PATH = "HKUST-Audio/xcodec2"

# Global model instances (loaded once at startup)
tokenizer = None
llasa_model = None
xcodec2_model = None

def load_models():
    global tokenizer, llasa_model, xcodec2_model
    if tokenizer is None:
        print("Loading Tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(LLASA_MODEL_NAME, token=HF_TOKEN)
    if llasa_model is None:
        print("Loading Llasa-1B Model...")
        llasa_model = AutoModelForCausalLM.from_pretrained(LLASA_MODEL_NAME, token=HF_TOKEN)
        llasa_model.eval().to('cuda')
    if xcodec2_model is None:
        print("Loading XCodec2 Model...")
        xcodec2_model = XCodec2Model.from_pretrained(XCODEC2_MODEL_PATH)
        xcodec2_model.eval().cuda()
    print("Models Loaded.")

def ids_to_speech_tokens(speech_ids):
    speech_tokens_str = []
    for speech_id in speech_ids:
        speech_tokens_str.append(f"<|s_{speech_id}|>")
    return speech_tokens_str

def extract_speech_ids(speech_tokens_str):
    speech_ids = []
    for token_str in speech_tokens_str:
        if token_str.startswith('<|s_') and token_str.endswith('|>'):
            num_str = token_str[4:-2]
            num = int(num_str)
            speech_ids.append(num)
        else:
            print(f"Unexpected token: {token_str}")
    return speech_ids

def clone_voice_tts(prompt_wav_path, target_text):
    global tokenizer, llasa_model, xcodec2_model

    if tokenizer is None or llasa_model is None or xcodec2_model is None:
        load_models() # Load models if not already loaded

    prompt_wav, sr = sf.read(prompt_wav_path)
    prompt_wav = torch.from_numpy(prompt_wav).float().unsqueeze(0).cuda()

    prompt_text = "This is prompt voice. " # You can add a default prompt text if needed.
    input_text = prompt_text + ' ' + target_text

    with torch.no_grad():
        vq_code_prompt = xcodec2_model.encode_code(input_waveform=prompt_wav)
        vq_code_prompt = vq_code_prompt[0,0,:]
        speech_ids_prefix = ids_to_speech_tokens(vq_code_prompt)

        formatted_text = f"<|TEXT_UNDERSTANDING_START|>{input_text}<|TEXT_UNDERSTANDING_END|>"

        chat = [
            {"role": "user", "content": "Convert the text to speech:" + formatted_text},
            {"role": "assistant", "content": "<|SPEECH_GENERATION_START|>" + ''.join(speech_ids_prefix)}
        ]

        input_ids = tokenizer.apply_chat_template(
            chat,
            tokenize=True,
            return_tensors='pt',
            continue_final_message=True
        ).to('cuda')
        speech_end_id = tokenizer.convert_tokens_to_ids('<|SPEECH_GENERATION_END|>')

        outputs = llasa_model.generate(
            input_ids,
            max_length=2048,
            eos_token_id=speech_end_id,
            do_sample=True,
            top_p=1,
            temperature=0.8,
        )

        generated_ids = outputs[0][input_ids.shape[1]-len(speech_ids_prefix):-1]
        speech_tokens = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
        speech_tokens = extract_speech_ids(speech_tokens)
        speech_tokens = torch.tensor(speech_tokens).cuda().unsqueeze(0).unsqueeze(0)

        gen_wav = xcodec2_model.decode_code(speech_tokens)

    return gen_wav[0, 0, :].cpu().numpy(), 16000 # Return waveform and sample rate


# Load models when this module is imported (at server startup)
load_models()
