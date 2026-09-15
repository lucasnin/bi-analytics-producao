import httpx

from app.ai.provider import AIProvider


class OllamaProvider(AIProvider):
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def explain(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(f"{self.base_url}/api/generate", json={"model": self.model, "prompt": prompt, "stream": False})
            response.raise_for_status()
            return response.json()["response"].strip()

