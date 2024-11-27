from planner.command.command_base import Command, StateChange, CommandExecutionResult

import logging
logger = logging.getLogger("LLMCommand")

import time # TODO: 仮の実装 後で消す
class MoveCommand(Command):
    def __init__(self) -> None:
        super().__init__(
            name="move",
            description='ロボットについている台車を動かして<location>に移動するコマンド、ロボット自身が移動するだけで、何か物やオブジェクトを掴む機能は無い',
            execute_args_description={"location": "<location>"},
            execute_required_known_arguments=["location"],
        )
    
    def execute(self, location) -> CommandExecutionResult:
        # TODO: 仮の実装　後で修正する
        import random
        result = False
        time.sleep(1) # TODO: 後で消す
        if result:
            status = "failure"
            message = f"{location}に移動できませんでした"
        else:
            status = "success"
            message = f"{location}に移動しました"

        return CommandExecutionResult(
            status=status,
            details=""
        )

class FindCommand(Command):
    def __init__(self) -> None:
        super().__init__(
            name="find",
            description='ロボットのカメラを用いて<object>を探すコマンド',
            execute_args_description={"object": "<object_name>"}
        )
        
    def execute(self, object) -> CommandExecutionResult:
        # TODO: 仮の実装　後で修正する
        import random
        result = random.choice([True, False])
        time.sleep(1) # TODO: 後で消す
        
        if not result:
            status = "failure"
            message = f"{object} が見つかりません"
        else:
            status = "success"
            message = f"{object}が見つかりました"
        
        return CommandExecutionResult(
            status=status,
            details=message
        )

class IntrofuceSelfCommand(Command):
    def __init__(self) -> None:
        super().__init__(
            name="introduce_self",
            description='自己紹介するコマンド',
            execute_args_description={"message": "<message>"}
        )
        
    def execute(self, message) -> CommandExecutionResult:
        return CommandExecutionResult(
            status="success"
        )

class SpeakMessageCommand(Command):
    def __init__(self) -> None:
        super().__init__(
            name="speak_message",
            description='ロボットのスピーカーを使用して<message>を発話する。',
            execute_args_description={"speak_message": "<message>"}
        )
    
    def execute(self, speak_message) -> CommandExecutionResult:
        time.sleep(1) # TODO: 後で消す
        return CommandExecutionResult(
            status="success"
        )   

class AskQuestionCommand(Command):
    def __init__(self) -> None:
        super().__init__(
            name="ask_question",
            description='<content>について、ロボットのスピーカーを用いてユーザー質問する。このコマンドを実行するには目の前に人が居る必要がある。',
            execute_args_description={"question": "<content>"}
        )
    
    def execute(self, question) -> CommandExecutionResult:
        time.sleep(1) # TODO: 後で消す
        return CommandExecutionResult(
            status="success"
        )

class PickUpObjectCommand(Command):
    def __init__(self) -> None:
        super().__init__(
            name="pick_up_object",
            description='ロボットのカメラとロボットについているアームを使用して物やオブジェクトを掴む',
            state_list=[],
            execute_args_description={"object": "<object_name>"},
            execute_required_known_arguments=["object"],
        )
        
    def execute(self, object) -> CommandExecutionResult:
        time.sleep(1) # TODO: 後で消す
        return CommandExecutionResult(
            status="success",
            state_changes=[StateChange("in_hand", True), StateChange("not_in_hand", False, args={})]
        )
    
class DropObjectCommand(Command):
    def __init__(self) -> None:
        super().__init__(
            name="drop_object",
            description='ロボットのカメラとロボットが持っているアームを使用して持っている物やオブジェクトを落とす',
            state_list=[
                
            ],
            execute_args_description={"object": "<object_name>"},
            execute_required_known_arguments=["object"],
        )
        
    def execute(self, object) -> CommandExecutionResult:
        time.sleep(1) # TODO: 後で消す
        return CommandExecutionResult(
            status="success",
            state_changes=[StateChange("in_hand", False), StateChange("not_in_hand", True, args={"x": str(object)})]
        )

class RecordCurrentLocationCommand(Command):
    def __init__(self) -> None:
        super().__init__(
            name="record_current_location",
            description='ロボットの現在位置を記録するコマンド',
        )
        
    def execute(self) -> CommandExecutionResult:
        time.sleep(1) # TODO: 後で消す
        return CommandExecutionResult(
            status="success"
        )
        
class ErrorCommand(Command):
    def __init__(self) -> None:
        super().__init__(
            name="error",
            description='"エラーを報告するコマンド、適切な実行可能なコマンドが見つからない場合に使用する',
            execute_args_description={"message": "<message>"}
        )
    
    def execute(self, message) -> CommandExecutionResult:
        return CommandExecutionResult(
            status="failure"
        )