import asyncio
from loguru import logger

async def convert_to_opus(input_path: str, output_path: str = "output.opus") -> str:
    """
    Convert MP3 to OPUS using ffmpeg
    ffmpeg -i SourceFile.mp3 -acodec libopus -ac 1 -ar 16000 TargetFile.opus
    """
    try:
        command = [
            "ffmpeg", "-y", "-i", input_path, 
            "-acodec", "libopus", 
            "-ac", "1", 
            "-ar", "16000", 
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"FFmpeg conversion failed: {stderr.decode()}")
            return None

        logger.info(f"FFmpeg conversion successful: {stdout.decode()}") 
        return output_path
    except Exception as e:
        logger.error(f"Audio conversion error: {e}")
        return None

async def get_audio_duration(file_path: str) -> int:
    """
    Get audio duration in milliseconds using ffprobe
    """
    try:
        command = [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"FFprobe failed: {stderr.decode()}")
            return 0
        
        duration_sec = float(stdout.decode().strip())
        logger.info(f"Audio duration: {duration_sec} seconds")
        return int(duration_sec * 1000)
    except Exception as e:
        logger.error(f"Get duration error: {e}")
        return 0