import logging
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')

from planner.llm_robot_planner import LLMRobotPlanner
from planner.commands.standard_commands import *
from utils.utils import read_key_value_pairs

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

