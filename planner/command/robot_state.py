from dataclasses import dataclass, field
from typing import Dict, Optional

from dataclasses import dataclass, field
@dataclass(frozen=True)
class StateChange():
    name: str
    active: bool
    args: Dict[str, Optional[str]] = field(default_factory=dict)
    
class RobotState:
    #uid: int = field(init=False)  # 自動インクリメント
    def __init__(
        self,
        name: str,
        description: str,
        args_description: Dict[str, Optional[str]] = {},
        initial_state: bool = False
    ):
        """
        
        Args:
            name (str): 名前
            description (str): 説明
            args (Dict[str, Optional[str]], optional): 引数. 
            initial_state (bool, optional): 初期化時に有効か無効か
        """
        self._name: str = name # 名前
        self._description: str = description # 説明
        self._args_description: Dict[str, Optional[str]] = args_description # 引数
        self.args: Dict[str, Optional[str]] = {}
        self.active: bool = initial_state  # 初期化時に有効か無効か  

    @property
    def name(self):
        return self._name
    @property
    def description(self):
        return self._description
    @property
    def args_description(self):
        return self._args_description
    
    def update(self, change: StateChange):
        self.active = change.active
        self.args = change.args
        
