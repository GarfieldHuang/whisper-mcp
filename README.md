# Python Whisper MCP

Local speech transcription MCP server using faster-whisper. Supports transcription, translation to English, JSON, text, SRT and VTT.

## Install

Double-click **`setup.bat`**. Nothing else is needed — if the machine has no
Python 3.10+, it downloads the official python.org installer and installs it
for the current user only, so no administrator rights are involved.

It prints the two paths you need for the MCP configuration when it finishes.

If you already have Python and prefer doing it by hand:

```bat
py -3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Recommended: 64-bit Python 3.10-3.12. The first call downloads the selected model.

### Corporate networks

The first call fetches the model from HuggingFace. Where a MITM proxy
intercepts TLS, its root certificate lives only in the Windows certificate
store, not in the bundle `certifi` ships, so the download fails with
`CERTIFICATE_VERIFY_FAILED: self signed certificate in certificate chain`.

`server.py` calls `truststore.inject_into_ssl()` at startup, which switches
Python over to the OS certificate store and makes the download work. Keep
`truststore` in `requirements.txt`.

To avoid downloading on every machine, pre-fetch the model once and point
`WHISPER_DOWNLOAD_ROOT` at a shared folder.

## MCP import parameters

- transport: `stdio`
- command: `D:\my_project\whisper-mcp\.venv\Scripts\python.exe`
- args: `["D:\\my_project\\whisper-mcp\\server.py"]`
- optional env: `WHISPER_MODEL=small`, `WHISPER_DEVICE=auto`, `WHISPER_COMPUTE_TYPE=default`
- optional env: `WHISPER_DOWNLOAD_ROOT=D:\models\whisper`
- optional env: `WHISPER_ZH_CONVERT=s2twp` (Traditional Chinese output, see below)

See `mcp.json.example` and `mcp_config.yaml.example`.

### my-agent GUI (新增 MCP Server dialog)

| Field | Value |
|---|---|
| 名稱 | `whisper` |
| 傳輸方式 | `stdio` |
| 指令 | `D:\my_project\whisper-mcp\.venv\Scripts\python.exe` |
| 參數 | `D:\my_project\whisper-mcp\server.py` |
| SSE URL | leave empty (stdio only) |
| inject | leave empty |

`inject` is for credentials the model should never see — this server needs none.

The dialog has no `env` field, so `WHISPER_MODEL` and friends cannot be set
there. The defaults (`small` / `auto` / `default`) apply. To change them, edit
`~/.my-agent/mcp_config.yaml` directly and add an `env:` block as shown in
`mcp_config.yaml.example`.

Claude Code command:

```bat
claude mcp add whisper -- "D:\my_project\whisper-mcp\.venv\Scripts\python.exe" "D:\my_project\whisper-mcp\server.py"
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
- `zh_convert`: Chinese script conversion, see below

## Traditional Chinese

Whisper's Chinese training data is overwhelmingly Simplified, so raw output is
Simplified regardless of the speaker. This server converts Chinese results to
Traditional Chinese (Taiwan) with OpenCC before returning them.

Conversion runs after recognition, so it never affects accuracy — and it only
applies when the detected language is `zh` and the task is transcription.
`whisper_translate_to_english` output is untouched.

| Value | Result for `这个软件的默认设置` |
|---|---|
| `s2twp` (default) | 這個**軟體**的**預設****設定** — Taiwan vocabulary |
| `s2tw` | characters only |
| `s2t` | generic Traditional |
| `off` | no conversion |

Set the default with `WHISPER_ZH_CONVERT`, or override per call with the
`zh_convert` argument. If `opencc` is missing or the config name is invalid,
conversion is skipped silently and the raw output is returned.

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
npx @modelcontextprotocol/inspector "D:\my_project\whisper-mcp\.venv\Scripts\python.exe" "D:\my_project\whisper-mcp\server.py"
```
