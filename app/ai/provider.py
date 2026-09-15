from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    async def explain(self, prompt: str) -> str: ...

