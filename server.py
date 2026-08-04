#!/usr/bin/env python3
from __future__ import annotations
import json, os, threading
from pathlib import Path
# 公司網路常以中間人 proxy 攔截 TLS，其根憑證只裝在 Windows 憑證
# 存放區，不在 certifi 內建的清單裡，於是首次下載模型會失敗在
# CERTIFICATE_VERIFY_FAILED。truststore 讓 Python 改用作業系統的
# 憑證存放區，HuggingFace 下載才過得去。裝不到就照原本的行為跑。
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

from faster_whisper import WhisperModel

# mcp 2.0 把 FastMCP 改名為 MCPServer 並移到 mcp.server 底下。
# 兩者的 .tool() 與 .run() 介面相同，這裡同時相容新舊版。
try:
    from mcp.server import MCPServer as _Server   # mcp >= 2.0
except ImportError:
    from mcp.server.fastmcp import FastMCP as _Server   # mcp 1.x

mcp = _Server("whisper")
DEFAULT_MODEL = os.getenv("WHISPER_MODEL", "small")
DEFAULT_DEVICE = os.getenv("WHISPER_DEVICE", "auto")
DEFAULT_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "default")
DOWNLOAD_ROOT = os.getenv("WHISPER_DOWNLOAD_ROOT") or None
MAX_RESULT_CHARS = int(os.getenv("WHISPER_MAX_RESULT_CHARS", "120000"))
_models = {}
_lock = threading.Lock()

def get_model(model, device, compute_type):
    key = (model, device, compute_type)
    with _lock:
        if key not in _models:
            _models[key] = WhisperModel(model, device=device, compute_type=compute_type, download_root=DOWNLOAD_ROOT)
        return _models[key]

def stamp(seconds, srt=False):
    ms = max(0, round(seconds * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    sep = "," if srt else "."
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"

def render(result, fmt):
    if fmt == "json":
        return json.dumps(result, ensure_ascii=False, indent=2)
    if fmt == "text":
        return result["text"].strip() + "\n"
    if fmt == "srt":
        blocks = []
        for i, seg in enumerate(result["segments"], 1):
            blocks.append(f"{i}\n{stamp(seg['start'], True)} --> {stamp(seg['end'], True)}\n{seg['text'].strip()}")
        return "\n\n".join(blocks) + "\n"
    if fmt == "vtt":
        blocks = ["WEBVTT"]
        for seg in result["segments"]:
            blocks.append(f"{stamp(seg['start'])} --> {stamp(seg['end'])}\n{seg['text'].strip()}")
        return "\n\n".join(blocks) + "\n"
    raise ValueError("output_format must be json, text, srt, or vtt")

def run_whisper(audio_path, language, task, model, device, compute_type, beam_size, vad_filter, word_timestamps, initial_prompt, output_format, output_path):
    source = Path(audio_path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Audio/video file not found: {source}")
    if task not in {"transcribe", "translate"}:
        raise ValueError("task must be transcribe or translate")
    fmt = output_format.lower().strip()
    if fmt not in {"json", "text", "srt", "vtt"}:
        raise ValueError("output_format must be json, text, srt, or vtt")
    if not 1 <= beam_size <= 20:
        raise ValueError("beam_size must be between 1 and 20")
    selected_model = model.strip() or DEFAULT_MODEL
    selected_device = device.strip() or DEFAULT_DEVICE
    selected_compute = compute_type.strip() or DEFAULT_COMPUTE_TYPE
    whisper = get_model(selected_model, selected_device, selected_compute)
    iterator, info = whisper.transcribe(str(source), language=language.strip() or None, task=task, beam_size=beam_size, vad_filter=vad_filter, word_timestamps=word_timestamps, initial_prompt=initial_prompt.strip() or None)
    items, text = [], []
    for seg in iterator:
        item = {"id": seg.id, "start": round(seg.start, 3), "end": round(seg.end, 3), "text": seg.text}
        if word_timestamps and seg.words:
            item["words"] = [{"start": round(w.start, 3), "end": round(w.end, 3), "word": w.word, "probability": round(w.probability, 5)} for w in seg.words]
        items.append(item)
        text.append(seg.text)
    result = {"source": str(source), "model": selected_model, "task": task, "language": info.language, "language_probability": round(info.language_probability, 5), "duration": round(info.duration, 3), "text": "".join(text).strip(), "segments": items}
    output = render(result, fmt)
    if output_path.strip():
        destination = Path(output_path).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(output, encoding="utf-8")
        return json.dumps({"ok": True, "output_path": str(destination), "format": fmt, "language": info.language, "duration": round(info.duration, 3), "segments": len(items), "preview": result["text"][:1000]}, ensure_ascii=False, indent=2)
    if len(output) > MAX_RESULT_CHARS:
        return output[:MAX_RESULT_CHARS] + "\n\n[Result truncated. Use output_path to save the complete result.]"
    return output

@mcp.tool()
def whisper_transcribe(audio_path: str, language: str = "", model: str = "", device: str = "", compute_type: str = "", beam_size: int = 5, vad_filter: bool = True, word_timestamps: bool = False, initial_prompt: str = "", output_format: str = "json", output_path: str = "") -> str:
    """Transcribe a local audio/video file. Formats: json, text, srt, vtt."""
    return run_whisper(audio_path, language, "transcribe", model, device, compute_type, beam_size, vad_filter, word_timestamps, initial_prompt, output_format, output_path)

@mcp.tool()
def whisper_translate_to_english(audio_path: str, language: str = "", model: str = "", device: str = "", compute_type: str = "", beam_size: int = 5, vad_filter: bool = True, word_timestamps: bool = False, initial_prompt: str = "", output_format: str = "json", output_path: str = "") -> str:
    """Translate speech in a local audio/video file into English."""
    return run_whisper(audio_path, language, "translate", model, device, compute_type, beam_size, vad_filter, word_timestamps, initial_prompt, output_format, output_path)

@mcp.tool()
def whisper_server_info() -> str:
    """Show defaults, formats, and common model names."""
    return json.dumps({"engine": "faster-whisper", "default_model": DEFAULT_MODEL, "default_device": DEFAULT_DEVICE, "default_compute_type": DEFAULT_COMPUTE_TYPE, "download_root": DOWNLOAD_ROOT, "formats": ["json", "text", "srt", "vtt"], "common_models": ["tiny", "base", "small", "medium", "large-v3", "distil-large-v3", "turbo"], "loaded_models": [list(k) for k in _models]}, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    mcp.run(transport="stdio")
