# llm-robot-Planning


[用語説明]

Instraction:
    最初にロボットに与える指示

Task:
    与えられた指示を内容ごとに複数のタスクに分解する。タスクとはその１つの単位

Command: 
    最小の実行単位、Commandに動作の内容を定義する。
    LLMRobotPlanerはcommandを組み合わせてタスクを実行する

Record: 
    Instraction, Task, Command, etc..など１つの指示についての全ての内容や履歴を保持する

Database:
    データベース、過去のRecordや知識(オブジェクトの位置や場所の位置など)を保持している。









