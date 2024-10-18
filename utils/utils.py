import re
import json
from typing import Dict, Union, Tuple

def read_key_value_pairs(file_path: str) -> Dict[str, str]:
    """
    指定されたファイルパスからキーと値のペアを読み取り、辞書として返します。

    Args:
        file_path (str): 読み込むファイルのパス

    Returns:
        dict: キーと値のペアを格納した辞書
    """
    key_value_pairs: Dict[str, str] = {}
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                # 引用符で囲まれている場合は、引用符を取り除く
                if value.startswith('"') and value.endswith('"') or \
                   value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                key_value_pairs[key] = value
    return key_value_pairs



def replace_placeholders(input_string: str, replacements: Dict[str, str], symbol: Union[str, Tuple[str, str]] = ("{", "}")):
    """
    カスタム記号で囲まれた部分文字列の置換を行う関数。
    
    Args:
        input_string (str): カスタム記号で囲まれた部分文字列を含む入力文字列。
        replacements (dict): カスタム記号で囲まれた部分文字列の置換値を含む辞書。
        start_symbol (str): 部分文字列を囲むために使用されるカスタム開始記号。
        end_symbol (str): 部分文字列を囲むために使用されるカスタム終了記号。
        
    Returns:
        str: カスタム記号で囲まれた部分文字列が辞書から対応する値に置換された入力文字列。
    """
    if isinstance(symbol, tuple) and len(symbol) == 2:
        start_symbol, end_symbol = symbol
    elif isinstance(symbol, str):
        start_symbol = symbol
        end_symbol = symbol
    else:
        raise ValueError("symbol must be a string or a tuple of two strings")
    
    pattern = re.compile(f'{re.escape(start_symbol)}(.*?){re.escape(end_symbol)}')

    def replace(match):
        key = match.group(1)
        return replacements.get(key, match.group(0))

    return pattern.sub(replace, input_string)


def pretty_print_nested_dict(nested_dict: dict):
  """入れ子になっているdictを綺麗にインデントをつけてstringで出力する関数

  Args:
    nested_dict: 入れ子になっているdict

  Returns:
    綺麗にインデントされたstring
  """
  return json.dumps(nested_dict, indent=2, ensure_ascii=False)


# def remove_json_markers(self, json_str):
#     """
#     生成AIのJSON形式の文字列の出力結果に現れるマーカーを削除して返す関数
#     """
#     return json_str.replace('JSON', '').replace('json', '').replace('```', '')
    
# def json_string_to_dict(self, json_str):
#     """
#     JSON形式の文字列をPythonの辞書に変換する関数
#     """
#     json_str = self.remove_json_markers(json_str)
#     result = json.loads(json_str)
#     return result

# def convert_ai_response_to_dict(self, response):
#     """
#     生成AIのレスポンスからPythonの辞書形式に変換して返す関数。
#     """
#     if response.type == "json":
#         result = self.json_string_to_dict(response.content)
#     else:
#         raise TypeError(f"Unsupported response type: {response.type}")
#     return result

# def get_ai_response(self, question, json_keys: List[str]):
#     """
#     生成AIのレスポンスをJSON形式で生成し、Pythonの辞書形式に変換して返す関数。
#     """
#     prompt = self.adjust_ai_prompt_json(json_keys)
#     content = prompt + question
#     ai_response = self.ai.generate_content(content)
#     response = AIResponse(content=ai_response, type="json")
#     response_dict = self.convert_ai_response_to_dict(response)
#     return response_dict

# def adjust_ai_prompt_json(self, keys: List[str]):
#     """
#     json形式で生成AIに返させる為のプロンプトを生成する関数。
#     """
#     s = ""
#     for key in keys:
#         s += f'  {key}: "value"\n'
#     replace_dict = { "json_keys_and_values": s }
    
#     return self.replace_placeholders(
#         input_string=CONST.GENERATE_AI_PROMPT_JSON, 
#         replacements=replace_dict,
#     )

        
        