from typing import Union, Dict, Literal, Optional
from abc import ABC, abstractmethod
import json
import logging # TODO: 後で削除

import google.generativeai as genai
#from google.generativeai import GenerationConfig

from utils.json import fix_and_parse_json


class GenAIWrapper(ABC):
    @abstractmethod
    def generate_content(self, prompt, model=None, *args, **kwargs) -> str:
        pass
    
class OpenAIWrapper(GenAIWrapper):
    pass

class GeminiWrapper(GenAIWrapper):
    def __init__(self, api_key, model_name, *args, **kwargs):
        genai.configure(api_key=api_key, *args, **kwargs)
        self.model = genai.GenerativeModel(model_name)
        
    def generate_content(self, prompt, *args, **kwargs) -> str:
        response = self.model.generate_content(prompt, *args, **kwargs)
        return response.text
    
class UnifiedAIRequestHandler:
    def __init__(
        self,
        api_keys: Dict[Union[Literal["google"], Literal["openai"]], str],
        #default_model_name: Optional[str] = None,
        ):
        
        self._models: dict[str, GenAIWrapper] = {}
        self.api_keys = api_keys
        #self.default_model_name = default_model_name
        
        # check api_keys and get model_lists
        for service_name, api_key in api_keys.items():
            if service_name == "google":
                genai.configure(api_key=api_key)
                s = ""
                for m in genai.list_models():
                    s += m.name + "\n" 
                logging.debug(s)
            elif service_name == "openai":
                raise NotImplementedError("openai is not supported yet")
            else:
                raise ValueError(f"service_name {service_name} is not supported")
        
    def generate_content(self, prompt, model_name: Optional[str]=None, *args, **kwargs) -> str:
        return self._get_model(model_name, "generate_content").generate_content(prompt, *args, **kwargs)
    
    def generete_content_v2(
        self, 
        prompt, 
        model_name: Optional[str] = None,
        response_type: Optional[Literal["json", "any"]] = None,
        convert_type: Optional[Literal["dict", "list", "none"]] = None,
        *args,
        **kwargs,
    ) -> str | list | dict:
        """
        
        Args:
            prompt: str 
            model_name: None | str  生成に使用するモデル
            
            :生成結果を特定のpythonオブジェクトに変換する場合:
            response_type: None | "json" | "any"  生成結果に予想される文字列の形式
            convert_type: None | "dict" | "list" | "none"  変換後の形式
        
        returns:
            generate_content: str | list | dict  生成結果
        """
        
        response_text = self.generate_content(prompt, model_name, *args, **kwargs)
        
        if (convert_type is not None and convert_type.lower() != "none" 
            and response_type is not None and response_type.lower() != "any"):
                # convert 
                if response_type.lower() == "json":
                    try:
                        py_obj = json.dumps(response_text)
                    except json.JSONDecodeError:
                        py_obj = fix_and_parse_json(response_text)
                else:
                    raise ValueError(f"response type: '{response_type}' is not supported")
                # response type check
                if convert_type.lower() == "dict":
                    if isinstance(py_obj, dict):
                        pass
                    else:
                        raise ValueError()
                elif convert_type.lower() == "list":
                    if isinstance(convert_type, list):
                        pass
                    else:
                        raise ValueError()
                else:
                    raise ValueError()
                
                response = py_obj
        else:
            response = response_text
        return response


    def _get_model(self, model_name, supported_generation_methods) -> GenAIWrapper:
        # TODO: 後で実装
        if not self._models:
            logging.debug("initializing models: 'models/gemini-1.0-pro-latest'") # TODO: 後で削除
            self._models["models/gemini-1.0-pro-latest"] = GeminiWrapper(self.api_keys["google"], "models/gemini-1.0-pro-latest")
        return self._models["models/gemini-1.0-pro-latest"]

