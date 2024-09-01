from planner.command_base import CommandBase, CommandExecutionResult

import logging
logger = logging.getLogger("LLMCommand")


class MoveCommand(CommandBase):
    def __init__(self) -> None:
        super().__init__(
            name="move",
            discription='ロボットについている台車を動かして<location>に移動するコマンド、ロボット自身が移動するだけで、何か物やオブジェクトを掴む機能は無い',
            execute_args_discription={"location": "<location>"},
            execute_required_known_arguments=["location"],
        )
    
    def execute(self, location) -> CommandExecutionResult:
        # TODO: 仮の実装　後で修正する
        import random
        result = random.choice([True, False])
        
        if result:
            status = "failed"
        else:
            status = "succeeded"
        
        return CommandExecutionResult(
            status=status,
            message=""
        )

class FindCommand(CommandBase):
    def __init__(self) -> None:
        super().__init__(
            name="find",
            discription='ロボットのカメラを用いて見つける',
            execute_args_discription={"object": "<object_name>"}
        )
        
    def execute(self, object) -> CommandExecutionResult:
        # TODO: 仮の実装　後で修正する
        import random
        result = random.choice([True, False])
        
        if result:
            status = "failed"
            message = f"{object} が見つかりません"
        else:
            status = "succeeded"
            message = "object found"
        
        return CommandExecutionResult(
            status=status,
            message=""
        )

class GetSelfHistoryCommand(CommandBase):
    def __init__(self) -> None:
        super().__init__(
            name="get_self_history",
            discription='自身の行動履歴を取得するコマンド',
            execute_args_discription={"target": "<content>"}
        )
        
    def execute(self, target) -> CommandExecutionResult:
        return CommandExecutionResult(
            status="succeeded"
        )

class IntrofuceSelfCommand(CommandBase):
    def __init__(self) -> None:
        super().__init__(
            name="introduce_self",
            discription='自己紹介するコマンド',
            execute_args_discription={"message": "<message>"}
        )
        
    def execute(self, message) -> CommandExecutionResult:
        return CommandExecutionResult(
            status="succeeded"
        )

class SpeakMessageCommand(CommandBase):
    def __init__(self) -> None:
        super().__init__(
            name="speak_message",
            discription='<content>について、ロボットのスピーカーを用いて発話する。 このコマンドは主にユーザーに対して発話、回答、応答、説明、伝達を行う為に用いる',
            execute_args_discription={"speak_message": "<message>"}
        )
    
    def execute(self, speak_message) -> CommandExecutionResult:
        return CommandExecutionResult(
            status="succeeded"
        )   

class AskQuestionCommand(CommandBase):
    def __init__(self) -> None:
        super().__init__(
            name="ask_question",
            discription='<content>について、ロボットのスピーカーを用いてユーザー質問する。このコマンドを実行するには目の前に人が居る必要がある。',
            execute_args_discription={"question": "<content>"}
        )
    
    def execute(self, question) -> CommandExecutionResult:
        return CommandExecutionResult(
            status="succeeded"
        )

class PickUpObjectCommand(CommandBase):
    def __init__(self) -> None:
        super().__init__(
            name="pick_up_object",
            discription='ロボットのカメラとロボットについているアームを使用して物やオブジェクトを掴む',
            execute_args_discription={"object": "<object_name>"},
            execute_required_known_arguments=["object"],
        )
        
    def execute(self, object) -> CommandExecutionResult:
        return CommandExecutionResult(
            status="succeeded"
        )
        
class ErrorCommand(CommandBase):
    def __init__(self) -> None:
        super().__init__(
            name="error",
            discription='"エラーを報告するコマンド、適切な実行可能なコマンドが見つからない場合に使用する',
            execute_args_discription={"message": "<message>"}
        )
    
    def execute(self, message) -> CommandExecutionResult:
        return CommandExecutionResult(
            status="succeeded"
        )