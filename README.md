# Python Whisper MCP

Local speech transcription MCP server using faster-whisper. Supports transcription, translation to English, JSON, text, SRT and VTT.

## Install

Run `setup.bat`, or:

```bat
py -3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Recommended: 64-bit Python 3.10-3.12. The first call downloads the selected model.

## MCP import parameters

- transport: `stdio`
- command: `D:\my_project\my-agent\whisper-mcp\.venv\Scripts\python.exe`
- args: `["D:\\my_project\\my-agent\\whisper-mcp\\server.py"]`
- optional env: `WHISPER_MODEL=small`, `WHISPER_DEVICE=auto`, `WHISPER_COMPUTE_TYPE=default`
- optional env: `WHISPER_DOWNLOAD_ROOT=D:\models\whisper`

See `mcp.json.example` and `mcp_config.yaml.example`.

Claude Code command:

```bat
claude mcp add whisper -- "D:\my_project\my-agent\whisper-mcp\.venv\Scripts\python.exe" "D:\my_project\my-agent\whisper-mcp\server.py"
claude mcp list
```

Remove with `claude mcp remove whisper`.

## Tools

- `whisper_transcribe`: transcribes a local audio/video file.
- `whisper_translate_to_english`: translates speech to English.
- `whisper_server_info`: displays server defaults.

Transcription arguments:

- `audio_path` required absolute path
- `language`: `zh`, `en`, `ja`, etc.; empty means auto detect
- `model`: `tiny`, `base`, `small`, `medium`, `large-v3`, `turbo`
- `device`: `auto`, `cpu`, `cuda`
- `compute_type`: `default`, `int8`, `float16`
- `beam_size`: 1-20
- `vad_filter`: silence filtering
- `word_timestamps`: include word timestamps
- `initial_prompt`: names and domain terminology
- `output_format`: `json`, `text`, `srt`, `vtt`
- `output_path`: save complete output to a local file

Example tool input:

```json
{
  "audio_path": "D:\\audio\\meeting.mp3",
  "language": "zh",
  "model": "small",
  "vad_filter": true,
  "output_format": "srt",
  "output_path": "D:\\audio\\meeting.srt"
}
```

CPU recommendation: `small`, `cpu`, `int8`. NVIDIA GPU: `large-v3` or `turbo`, `cuda`, `float16`.

Test with MCP Inspector:

```bat
npx @modelcontextprotocol/inspector "D:\my_project\my-agent\whisper-mcp\.venv\Scripts\python.exe" "D:\my_project\my-agent\whisper-mcp\server.py"
```
