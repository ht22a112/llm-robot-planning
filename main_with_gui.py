
from planner.llm_robot_planner import LLMRobotPlanner
from planner.command.commands.standard_commands import *
from utils.utils import read_key_value_pairs

import threading
import logging

# Logger
LLM_logger = logging.getLogger("LLMRobotPlanner")
LLM_logger.setLevel(logging.DEBUG)
LLM_command_logger = logging.getLogger("LLMCommand")
LLM_command_logger.setLevel(logging.DEBUG)

# LLM Robot Planner 実行        
def process_llm_robot_planner():
    planner = LLMRobotPlanner(
        # API Keyの設定
        api_keys={ 
            "google": read_key_value_pairs("key.env")["GEMINI_API_KEY"],
        },
        commands=[
            MoveCommand(),
            FindCommand(),
            IntrofuceSelfCommand(),
            SpeakMessageCommand(),
            AskQuestionCommand(),
            PickUpObjectCommand(),
            DropObjectCommand(),
            ErrorCommand(),
        ]
    )

    planner.initialize(
        input("What do you want to do?: ")
    )

    for _ in planner.process():
        LLM_logger.info("")

# Console用 Logger
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
console_handler.setLevel(logging.DEBUG)
LLM_logger.addHandler(console_handler)



from flet import Page, app
from gui.view.real_time_info_view import LLMRobotPlannerRealTimeInfoView
from gui.logger_handler import LoggingGUIHandler
from logger.logger import LLMRobotPlannerLogSystem
log_system = LLMRobotPlannerLogSystem()


def main(page: Page):
    planner_info = LLMRobotPlannerRealTimeInfoView(page=page)
    log_system.add_handler(LoggingGUIHandler(planner_info))
    page.add(planner_info)
    
    # LLM Robot Planner スレッドの開始
    llm_robot_planner = threading.Thread(target=process_llm_robot_planner, daemon=True)
    llm_robot_planner.start()

app(target=main)









