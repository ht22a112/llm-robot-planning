from llm.command_base import CommandBase, CommandExecutionResult

class MoveCommand(CommandBase):
    def __init__(self) -> None:
        super().__init__(
            name="move",
            discription='"move", args: "location": "<location>"  # <location>に移動するコマンド'
        )
         
    def execute(self) -> CommandExecutionResult:
        return CommandExecutionResult(
            status="succeeded"
        )

class FindCommand(CommandBase):
    def __init__(self) -> None:
        super().__init__(
            name="find",
            discription='"find", args: "object": "<object_name>"  # <object_name>をロボットのカメラを用いて見つける'
        )
        
    def execute(self) -> CommandExecutionResult:
        return CommandExecutionResult(
            status="succeeded"
        )

class GetSelfHistoryCommand(CommandBase):
    def __init__(self) -> None:
        super().__init__(
            name="get_self_history",
            discription='"get_self_history", args: "target": "<content>"  # 自身の行動履歴を取得するコマンド'
        )
        
    def execute(self) -> CommandExecutionResult:
        return CommandExecutionResult(
            status="succeeded"
        )

class IntrofuceSelfCommand(CommandBase):
    def __init__(self) -> None:
        super().__init__(
            name="introduce_self",
            discription='"introduce_self", args: "message": "<message>"  # 自己紹介するコマンド'
        )
    
    def execute(self) -> CommandExecutionResult:
        return CommandExecutionResult(
            status="succeeded"
        )

class SpeakMessageCommand(CommandBase):
    def __init__(self) -> None:
        super().__init__(
            name="speak_message",
            discription='"speak_message", args: "message": "<content>"  # <content>について、ロボットのスピーカーを用いて発話する。 このコマンドは主にユーザーに対して発話、回答、応答、説明、伝達を行う為に用いる'
        )
    
    def execute(self) -> CommandExecutionResult:
        return CommandExecutionResult(
            status="succeeded"
        )   
    
class ErrorCommand(CommandBase):
    def __init__(self) -> None:
        super().__init__(
            name="error",
            discription='"error", args: "message": "<message>"  # エラーを報告するコマンド、適切な実行可能なコマンドが見つからない場合に使用する'
        )
    
    def execute(self) -> CommandExecutionResult:
        return CommandExecutionResult(
            status="succeeded"
        )