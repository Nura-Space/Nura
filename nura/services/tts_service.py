import base64
import json
import uuid
import asyncio
import requests
from loguru import logger
from typing import Optional

from nura.services.tts import TTSService


class VolcengineTTS(TTSService):
    """Volcengine TTS implementation using the Ark API"""
    def __init__(self, config):
        self.config = config.get("tts_config", {})
        self.appid = self.config.get("appid")
        self.access_token = self.config.get("access_token")
        self.cluster = self.config.get("cluster")
        self.voice_type = self.config.get("voice_type")
        self.api_url = self.config.get("api_url")
        self.header = {"Authorization": f"Bearer;{self.access_token}"}

    async def generate_audio(self, text: str, output_path: str = "output.mp3") -> Optional[str]:
        """
        Generate MP3 audio from text using Volcengine TTS API
        Returns the path to the generated MP3 file
        """
        request_json = {
            "app": {
                "appid": self.appid,
                "token": "access_token",
                "cluster": self.cluster
            },
            "user": {
                "uid": "388808087185088"
            },
            "audio": {
                "voice_type": self.voice_type,
                "encoding": "mp3",
                "speed_ratio": 1.0,
                "volume_ratio": 1.0,
                "pitch_ratio": 1.0,
            },
            "request": {
                "reqid": str(uuid.uuid4()),
                "text": text,
                "text_type": "plain",
                "operation": "query",
                "with_frontend": 1,
                "frontend_type": "unitTson"
            }
        }

        try:
            response = await asyncio.to_thread(
                requests.post, 
                self.api_url, 
                json.dumps(request_json), 
                headers=self.header
            )
            
            resp_json = response.json()
            if "data" in resp_json:
                data = resp_json["data"]
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(data))
                return output_path
            else:
                logger.error(f"TTS API Error: {resp_json}")
                return None
        except Exception as e:
            logger.error(f"TTS Generation Failed: {e}")
            return None
