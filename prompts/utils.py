from typing import Union, Tuple, Dict

from utils.utils import replace_placeholders
from prompts.prompt_texts.system_prompt import *
from prompts.prompt_texts.retrieval_doc import *
from prompts.prompt_texts.result_evaluate import *

def get_prompt(
    prompt_name: str,
    replacements: Dict[str, str] = {},
    symbol: Union[str, Tuple[str, str]] = ("{", "}"),
) -> str:
    """
    プロンプトを取得する
    
    Args:
        prompt_name (str): プロンプト名
        
        <promptの文字列を置換する場合>
        replacements (dict, optional): 置換値を含む辞書  
        symbol (Union[str, Tuple[str, str]], optional): 部分文字列を囲むために使用されるカスタム記号
    """
    if prompt_name == "interpret_instruction":
        prompt = interpret_instruction_prompt
    elif prompt_name == "generate_commands_from_task":
        prompt = generate_commands_from_task_prompt
    elif prompt_name == "GENERATE_QUERY":
        prompt = GENERATE_QUERY_PROMPT
    elif prompt_name == "EVALUATE_RESULT":
        prompt = RESULT_EVALUATE_PROMPT
    else:
        raise ValueError(f"prompt_name {prompt_name} is not supported")
    
    if replacements:
        return replace_placeholders(prompt, replacements=replacements, symbol=symbol)
    else:
        return prompt
        