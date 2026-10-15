import base64, io, os, subprocess, tempfile, threading
from pathlib import Path
import runpod
from huggingface_hub import hf_hub_download
from PIL import Image, UnidentifiedImageError

MODEL_DIR = Path(os.environ.get("MODEL_DIR", "/tmp/qwen-models"))
SD_CLI = os.environ.get("SD_CLI", "/sd.cpp/bin/sd-cli")
SIGMAS = "1.0,0.978453,0.95418,0.926626,0.89508,0.845148,0.704534,0.414568,0.0"
ASSETS = {
 "denoiser": ("AtomicChat/Qwen-Image-2.1-Turbo-GGUF", "Qwen-Image-2.1-Turbo-AD-Q4_K.gguf"),
 "encoder": ("AtomicChat/Qwen-Image-2.1-Turbo-Uncensored-GGUF", "Qwen-Image-2.1-Turbo-Uncensored-AD-Q4_K.gguf"),
 "vision": ("AtomicChat/Qwen-Image-2.1-Turbo-Uncensored-GGUF", "mmproj-Qwen-Image-2.1-Turbo-Uncensored-F16.gguf"),
 "vae": ("Comfy-Org/Qwen-Image-2.1", "vae/qwen_image_2.1_vae_bf16.safetensors"),
}
_paths, _lock = {}, threading.Lock()

def models():
 global _paths
 with _lock:
  if _paths and all(Path(p).is_file() for p in _paths.values()): return _paths
  MODEL_DIR.mkdir(parents=True, exist_ok=True)
  result = {}
  for key, (repo, filename) in ASSETS.items():
   print(f"Downloading/checking {repo}/{filename}", flush=True)
   result[key] = hf_hub_download(repo_id=repo, filename=filename, local_dir=str(MODEL_DIR / key))
  _paths = result
  return result

def save_input(value, path):
 if not value: raise ValueError("Image edit mode requires image_base64.")
 if value.startswith("data:"): value = value.split(",", 1)[1]
 if len(value) > 12_000_000: raise ValueError("Image too large; resize it to under about 8 MB.")
 try:
  raw = base64.b64decode(value, validate=True)
  with Image.open(io.BytesIO(raw)) as im:
   im = im.convert("RGB")
   im.thumbnail((1536, 1536))
   im.save(path, format="PNG")
 except (ValueError, UnidentifiedImageError) as e:
  raise ValueError("Could not read image. Upload PNG, JPEG, or WebP.") from e

def handler(event):
 data = event.get("input", {})
 try:
  prompt = str(data.get("prompt", "")).strip()
  mode = str(data.get("mode", "text")).lower()
  if not prompt: raise ValueError("Prompt is required.")
  if mode not in ("text", "edit"): raise ValueError("mode must be text or edit.")
  width, height = int(data.get("width", 768)), int(data.get("height", 768))
  if not (512 <= width <= 1280 and 512 <= height <= 1280): raise ValueError("Width/height must be 512–1280.")
  width, height = width // 32 * 32, height // 32 * 32
  seed = int(data.get("seed", -1))
  m = models()
  with tempfile.TemporaryDirectory(prefix="qwen-job-") as td:
   td = Path(td); output = td / "result.png"; input_img = td / "input.png"
   if mode == "edit": save_input(data.get("image_base64", ""), input_img)
   cmd = [SD_CLI, "--diffusion-model", m["denoiser"], "--llm", m["encoder"], "--vae", m["vae"],
          "--steps", "8", "--cfg-scale", "1.0", "--sampling-method", "euler", "--sigmas", SIGMAS,
          "-W", str(width), "-H", str(height), "--offload-to-cpu", "-p", prompt, "-o", str(output)]
   if seed >= 0: cmd += ["--seed", str(seed)]
   if mode == "edit": cmd += ["--llm_vision", m["vision"], "-r", str(input_img)]
   run = subprocess.run(cmd, capture_output=True, text=True, timeout=int(os.environ.get("GENERATION_TIMEOUT_SECONDS", "1200")))
   if run.returncode: raise RuntimeError((run.stderr or run.stdout or "sd-cli failed")[-4000:])
   if not output.is_file(): raise RuntimeError("sd-cli returned without an image.")
   return {"image_base64": base64.b64encode(output.read_bytes()).decode("ascii"), "mime_type": "image/png",
           "width": width, "height": height, "mode": mode, "note": "Output is returned in memory; no gallery is saved."}
 except Exception as e:
  print(f"Job failed: {type(e).__name__}: {e}", flush=True)
  return {"error": str(e)}

if __name__ == "__main__":
 runpod.serverless.start({"handler": handler})
