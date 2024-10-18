from typing import Union, Dict, Literal, Optional, overload
import json
from utils.json_utils import fix_and_parse_json
from planner.llm.wrapper_base import GenAIWrapper
from planner.llm.wrappers.gemini import GeminiWrapper  # TODO: 後に削除

import logging
logger = logging.getLogger("GenAI")

from logger.logger import LLMRobotPlannerLogSystem
log = LLMRobotPlannerLogSystem()

class UnifiedAIRequestHandler:
    def __init__(
        self,
        api_keys: Dict[Union[Literal["google"], Literal["openai"]], str],
        #default_model_name: Optional[str] = None,
        ):
        
        self._models: dict[str, GenAIWrapper] = {}
        self.api_keys = api_keys
        #self.default_model_name = default_model_name
        
        # # check api_keys and get model_lists
        # for service_name, api_key in api_keys.items():
        #     if service_name == "google":
        #         genai.configure(api_key=api_key)
        #         s = ""
        #         for m in genai.list_models():
        #             s += m.name + "\n" 
        #         logger.debug(s)
        #     elif service_name == "openai":
        #         raise NotImplementedError("openai is not supported yet")
        #     else:
        #         raise ValueError(f"service_name {service_name} is not supported")
        
    def generate_content(self, prompt, model_name: Optional[str]=None, *args, **kwargs) -> str:
        return self._get_model(model_name, "generate_content").generate_content(prompt, *args, **kwargs)
    
    @overload
    def generate_content_v2(
        self, 
        prompt: str, 
        response_type: None = None,
        convert_type: None = None,
        model_name: Optional[str] = None,
        *args,
        **kwargs
    ) -> str: ...

    @overload
    def generate_content_v2(
        self, 
        prompt: str, 
        response_type: Literal["json"] = "json",
        convert_type: Literal["dict"] = "dict",
        model_name: Optional[str] = None,
        *args,
        **kwargs
    ) -> dict: ...

    @overload
    def generate_content_v2(
        self, 
        prompt: str, 
        response_type: Literal["json"] = "json",
        convert_type: Literal["list"] = "list",
        model_name: Optional[str] = None,
        *args,
        **kwargs
    ) -> list: ...
    
    def generate_content_v2(
        self, 
        prompt: str, 
        response_type: Optional[Literal["json", "any"]] = None,
        convert_type: Optional[Literal["dict", "list", "none"]] = None,
        model_name: Optional[str] = None,
        *args,
        **kwargs
    ) -> Union[str, list, dict]:
        """
        生成コンテンツを取得し、必要に応じて変換します。

        Args:
            prompt: 生成のためのプロンプト
            model_name: 生成に使用するモデル（オプション）
            response_type: 予想される生成結果の形式 ("json" または "any")
            convert_type: 変換後の形式 ("dict", "list", または "none")

        Returns:
            生成結果（文字列、リスト、または辞書）
        """
        
        with log.span("LLM Generation") as span:
            span.input(prompt)
            response_text = self.generate_content(prompt, model_name, *args, **kwargs)
            
            if (convert_type is not None and convert_type.lower() != "none" 
                and response_type is not None and response_type.lower() != "any"):
                    # convert 
                    if response_type.lower() == "json":
                        try:
                            py_obj = json.loads(response_text)
                        except json.JSONDecodeError:
                            try:
                                py_obj = fix_and_parse_json(response_text)
                            except Exception as e:
                                raise Exception(f"{str(e)}\nresponse_text:{response_text}")
                    else:
                        raise ValueError(f"response type: '{response_type}' is not supported")
                    # response type check
                    if convert_type.lower() == "dict":
                        if isinstance(py_obj, dict):
                            pass
                        else:
                            raise ValueError(f"response type: '{type(py_obj)}' is not dict\n{response_text}")
                    elif convert_type.lower() == "list":
                        if isinstance(convert_type, list):
                            pass
                        else:
                            raise ValueError()
                    else:
                        raise ValueError()
                    
                    response = py_obj
                    span.output(json.dumps(response, indent=2, ensure_ascii=False))
            else:
                response = response_text
                span.output(response)
            
            return response


    def _get_model(self, model_name, supported_generation_methods) -> GenAIWrapper:
        # TODO: 後で実装
        model_name = "models/gemini-1.5-flash"
        if not self._models:
            logger.debug(f"initializing models: '{model_name}'") # TODO: 後で削除
            self._models[model_name] = GeminiWrapper(self.api_keys["google"], model_name)
        return self._models[model_name]

