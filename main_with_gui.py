
from llm.llm_robot_planner import LLMRobotPlanner
from llm.commands.standard_commands import *
from utils.utils import read_key_value_pairs

from flet import Page, app
from gui.gui import LLMRobotPlannerInfoView

import threading
import logging

# Logger
LLM_logger = logging.getLogger("LLMRobotPlanner")
LLM_logger.setLevel(logging.DEBUG)

class LogHandler(logging.Handler):
    def __init__(self, log_display: LLMRobotPlannerInfoView):
        super().__init__()
        self.log_display = log_display
        
        formatter = logging.Formatter('[%(levelname)s]\n%(message)s')
        self.setFormatter(formatter)
        self.setLevel(logging.INFO)

    def emit(self, record):
        log_entry = self.format(record)
        self.log_display.append(log_entry)
        
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
            GetSelfHistoryCommand(),
            IntrofuceSelfCommand(),
            SpeakMessageCommand(),
            ErrorCommand(),
        ]
    )

    planner.initialize(
        input("What do you want to do?: ")
    )

    for _ in planner.process():
        pass

# Console用 Logger
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
console_handler.setLevel(logging.DEBUG)
LLM_logger.addHandler(console_handler)

# LLM Robot Planner スレッドの開始
llm_robot_planner = threading.Thread(target=process_llm_robot_planner, daemon=True)
llm_robot_planner.start()

def main(page: Page):
    planner_info = LLMRobotPlannerInfoView(page=page)
    gui_handler = LogHandler(planner_info)
    LLM_logger.addHandler(gui_handler)
    page.add(planner_info)
    
app(target=main)









