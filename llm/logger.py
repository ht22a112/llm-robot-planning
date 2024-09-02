from typing import Optional
import json

def pretty_print_nested_dict(nested_dict):
  """入れ子になっているdictを綺麗にインデントをつけてstringで出力する関数

  Args:
    nested_dict: 入れ子になっているdict

  Returns:
    綺麗にインデントされたstring
  """
  return json.dumps(nested_dict, indent=2).encode('latin1').decode('unicode_escape')




from logger.logger import LLMRobotPlannerLogger

logger = LLMRobotPlannerLogger()

def log_llm(response, prompt: Optional[str] = None):
    if prompt is not None:
        logger.log("LLM Request", str(prompt))
        
    if isinstance(response, dict):
        response = pretty_print_nested_dict(response)
    else:
        response = str(response)
    logger.log("LLM Response", response)    

   
    
    