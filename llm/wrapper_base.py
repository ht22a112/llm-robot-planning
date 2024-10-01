from abc import ABC, abstractmethod

class GenAIWrapper(ABC):
    @abstractmethod
    def generate_content(self, prompt, model=None, *args, **kwargs) -> str:
        pass