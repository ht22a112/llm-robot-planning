import time
from collections import deque
import google.generativeai as genai
from google.generativeai import GenerationConfig
from planner.llm.gen_ai import GenAIWrapper

class GeminiWrapper(GenAIWrapper):
    def __init__(self, api_key, model_name, *args, **kwargs):
        genai.configure(api_key=api_key, *args, **kwargs)
        config = GenerationConfig(temperature=0.0)
        self.model = genai.GenerativeModel(model_name, generation_config=config)

        self._request_times = deque(maxlen=15)  # 直近15回のリクエスト時間を保持
        
    def generate_content(self, prompt, *args, **kwargs) -> str:
        self._throttle_requests()  # リクエスト制御
        
        response = self.model.generate_content(prompt, *args, **kwargs)
        return response.text
    
    def _throttle_requests(self):
        """
        リクエストを制御する
        15回のリクエストが60秒以内に行われた場合、Geminiの無料枠を超えない為に待機する
        """
        # 現在の時間を取得
        current_time = time.time()
        
        # リクエストの履歴を更新
        if len(self._request_times) == 15:
            # 15回分の記録がある場合、最初のリクエスト時間を確認
            if current_time - self._request_times[0] < 60:
                wait_time = 60 - (current_time - self._request_times[0])
                print(f"Rate limit reached. Waiting for {wait_time:.2f} seconds.")
                time.sleep(wait_time)
        
        # 現在の時間をリクエスト履歴に追加
        self._request_times.append(current_time)
