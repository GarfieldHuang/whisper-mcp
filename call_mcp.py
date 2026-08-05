import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
async def main():
    p = StdioServerParameters(command=r"D:\my_project\whisper-mcp\.venv\Scripts\python.exe", args=[r"D:\my_project\whisper-mcp\server.py"], env={"WHISPER_MODEL":"small","WHISPER_DEVICE":"cpu","WHISPER_COMPUTE_TYPE":"int8","WHISPER_ZH_CONVERT":"s2twp"})
    async with stdio_client(p) as (rd, wr):
        async with ClientSession(rd, wr) as sess:
            await sess.initialize()
            result = await sess.call_tool("whisper_transcribe", {"audio_path":r"D:\my_project\input與output\地端跑 DeepSeek-V4-Flash 0731 RTX PRO 6000 單卡 vram 96GB 實測：IQ2、IQ3 該選哪個_1080p.mp4","language":"zh","model":"small","device":"cpu","compute_type":"int8","beam_size":5,"vad_filter":True,"word_timestamps":False,"output_format":"srt","output_path":r"D:\my_project\input與output\地端跑 DeepSeek-V4-Flash 0731 RTX PRO 6000 單卡 vram 96GB 實測：IQ2、IQ3 該選哪個_逐字稿.srt","zh_convert":"s2twp"})
            print(result)
asyncio.run(main())
