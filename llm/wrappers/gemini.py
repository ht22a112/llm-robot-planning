import google.generativeai as genai
from google.generativeai import GenerationConfig

from llm.gen_ai import GenAIWrapper

class GeminiWrapper(GenAIWrapper):
    def __init__(self, api_key, model_name, *args, **kwargs):
        genai.configure(api_key=api_key, *args, **kwargs)
        #TODO: テスト用なのであとで消す
        config = GenerationConfig(temperature=0.0)
        self.model = genai.GenerativeModel(model_name, generation_config=config)
        
    def generate_content(self, prompt, *args, **kwargs) -> str:
        response = self.model.generate_content(prompt, *args, **kwargs)
        return response.text