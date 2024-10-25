from typing import Union, Dict, Literal, Optional, overload
import json
from utils.json_utils import fix_and_parse_json

class Parser():
    pass

class JsonParser(Parser):
    def __init__(self):
        pass
    
    @overload
    def parse(
        self, 
        text: str, 
        response_type: None = None,
        convert_type: None = None,
    ) -> str: ...

    @overload
    def parse(
        self, 
        text: str, 
        response_type: Literal["json"] = "json",
        convert_type: Literal["dict"] = "dict",
    ) -> dict: ...

    @overload
    def parse(
        self, 
        text: str,
        response_type: Literal["json"] = "json",
        convert_type: Literal["list"] = "list",
    ) -> list: ...
    
    def parse(
        self,
        text: str,
        response_type: Optional[Literal["json", "any"]] = None,
        convert_type: Optional[Literal["dict", "list", "none"]] = None
    ):
        if (convert_type is not None and convert_type.lower() != "none" 
            and response_type is not None and response_type.lower() != "any"):
                # convert 
                if response_type.lower() == "json":
                    try:
                        py_obj = json.loads(text)
                    except json.JSONDecodeError:
                        try:
                            py_obj = fix_and_parse_json(text)
                        except Exception as e:
                            raise Exception(f"{str(e)}\nresponse_text:{text}")
                else:
                    raise ValueError(f"response type: '{response_type}' is not supported")
                # response type check
                if convert_type.lower() == "dict":
                    if isinstance(py_obj, dict):
                        pass
                    else:
                        raise ValueError(f"response type: '{type(py_obj)}' is not dict\n{text}")
                elif convert_type.lower() == "list":
                    if isinstance(convert_type, list):
                        pass
                    else:
                        raise ValueError()
                else:
                    raise ValueError()
                
                response = py_obj
        else:
            response = text
                
        return response