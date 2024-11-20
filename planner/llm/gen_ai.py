from typing import Union, Dict, Literal, Optional
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
                
    def generate_content(
        self, 
        prompt: str, 
        model_name: Optional[str] = None,
        *args,
        **kwargs
    ) -> str:
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
        
        with log.span("LLM Generation",metadata={"model": "gemini-1.5-flash"}) as span:
            span.input(prompt)
            response_text = self._get_model(model_name, "generate_content").generate_content(prompt, *args, **kwargs)
            span.output(response_text)
            
            return response_text


    def _get_model(self, model_name, supported_generation_methods) -> GenAIWrapper:
        # TODO: 後で実装
        model_name = "models/gemini-1.5-flash"
        if not self._models:
            logger.debug(f"initializing models: '{model_name}'") # TODO: 後で削除
            self._models[model_name] = GeminiWrapper(self.api_keys["google"], model_name)
        return self._models[model_name]
