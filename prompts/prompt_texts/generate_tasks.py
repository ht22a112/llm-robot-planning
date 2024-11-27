GENERATE_TASKS = \
"""あなたはロボットのタスク計画を支援するアシスタントです。以下の指示を読み、タスクを分解してください。
- 指示が複数のステップに分けられる場合は、動作ごとタスクを分割してください。例えば、「机の上のリンゴを持ってきてください、それが終わったら次は玄関に人が居るか見てきて」という指示は、「リンゴを持ってくる」というタスクと「玄関に人が居るか確認する」というタスクにまず分割し、さらに「リンゴを持ってくる」タスクを「机に移動する」「リンゴを取る」「元の場所に戻る」「リンゴを渡す」といったタスクに動作ごとに細かく分割する必要があります。
- 必ず元の指示からステップごとに分割してタスクに変換するときに、情報が失われないように注意して分割すること。タスクから元の指示を推測できるようにしてください。
- タスクの分割には「まず何をすべきか、その次に何をすべきか」を１つずつ明確にすることが重要です。
- 必ず元の位置や現在位置に戻る必要があるか考えてください。必要であれば"元の位置"や"現在位置"に戻ってください！！
- 必ずユーザーに対して回答や返事を返す必要があるか考えてください。必要であればユーザーの元に戻り、回答や返事を返すようにタスクを構築してください！！
- ハルシネーションを行わないようにしてください

タスクには次の情報を含めてください：

task_sequence_number:（必須）タスクの実行順序を示す
task_description:（必須）タスクの具体的な内容を簡潔に記述してください。
task_additional_info:（任意）必要となる場合のみ補足情報を記述してください。
task_dependencies:（任意）このタスクが依存（実行に必要となる）する他のタスクとその理由、および必要なoutcomeをリスト化してください、複数あれば複数個書くこと。
  dependency_task_sequence_number: 依存（実行に必要となる）するタスクの番号(task_sequence_numberを示す)
  reason: 理由
  required_outcome_desired_information_uids: このタスクを実行するために必要なdesired_informationのuid
  required_outcome_desired_robot_state_uids: このタスクを実行するために必要なrobot_stateのuid
task_environmental_conditions:（任意）タスクを実行するために必要な条件を記述してください（物理的条件と情報条件）。
  "required_physical_conditions":（任意）物理的条件
  "required_information_conditions":（任意）情報条件
    "required_information_locations":（任意）必要となる場所の情報
    "required_information_objects":（任意）必要となるオブジェクトの情報
  
task_reason:（必須）このタスクを行う理由を記述してください。
task_outcome:（必須）タスクの完了条件を明示してください。以下の3つの情報を含めます：
  desired_information:（任意）このタスクで得られるべき情報、または保存する情報。
  desired_robot_state:（任意）タスク完了時にロボットが持つべき状態（必ず以下の候補一覧からのみ選択すること、該当しない場合は選択しない）。
指示:
「{{instruction}}」

desired_robot_state の候補一覧（これ以外の候補は選択しないこと）:
{{state_descriptions}}

出力は以下のJSONフォーマットで記述してください：

{
  "tasks": [
    {
      "task_sequence_number": "int",
      "task_description": "string",
      "task_additional_info": "string",
      "task_dependencies": [
        {
          "dependency_task_sequence_number": "int",
          "reason": "string",
          "required_outcome_desired_information_uids": ["int"],
          "required_outcome_desired_robot_state_uids": ["int"]
        }
      ],
      "task_environmental_conditions": {
        "required_physical_conditions": ["string"],
        "required_information_conditions": {
          "required_information_locations": ["string"],
          "required_information_objects": ["string"]
        }
      },
      "task_reason": "string",
      "task_outcome": {
        "desired_information": [
          {
            "uid": "int",
            "description": "string"
          }
        ],
        "desired_robot_state": [
          {
            "uid": "int",
            "state_name": "string",
            "state_args": [
                args1, args2, ...
            ]
          }
        ]
      }
    }
  ]
}
"""


REGENERATE_TASKS = \
"""あなたはロボットのタスクの再計画を支援するアシスタントです。以下の指示、実行したプラン、失敗の原因を読み、タスクをもう一度分解してください。
- 指示が複数のステップに分けられる場合は、動作ごとタスクを分割してください。例えば、「机の上のリンゴを持ってきてください、それが終わったら次は玄関に人が居るか見てきて」という指示は、「リンゴを持ってくる」というタスクと「玄関に人が居るか確認する」というタスクにまず分割し、さらに「リンゴを持ってくる」タスクを「机に移動する」「リンゴを取る」「元の場所に戻る」「リンゴを渡す」といったタスクに動作ごとに細かく分割する必要があります。
- 必ず元の指示からステップごとに分割してタスクに変換するときに、情報が失われないように注意して分割すること。タスクから元の指示を推測できるようにしてください。
- タスクの分割には「まず何をすべきか、その次に何をすべきか」を１つずつ明確にすることが重要です。
- 必ず元の位置や現在位置に戻る必要があるか考えてください。必要であれば"元の位置"や"現在位置"に戻ってください！！
- 必ずユーザーに対して回答や返事を返す必要があるか考えてください。必要であればユーザーの元に戻り、回答や返事を返すようにタスクを構築してください！！
- ハルシネーションを行わないようにしてください


「机の上のりんごを持ってきて」という指示を受けて以下のプランを生成してそのプランを実行したところ、タスク{{failed_task_id}}の実行に失敗しました。
指示から生成して実行したプラン:
{{execution_tasks}}
考えられる失敗の原因:
    失敗の原因: {{failed_cause}}

「机の上のりんごを持ってきて」を指示を遂行するために、タスク{{next_failed_task_id}}以降の内容を再生成してください

失敗の原因の解決方法: 
    解決方法: {{failed_task_solution}}

タスクには次の情報を含めてください：

task_sequence_number:（必須）タスクの実行順序を示す
task_description:（必須）タスクの具体的な内容を簡潔に記述してください。
task_additional_info:（任意）必要となる場合のみ補足情報を記述してください。
task_dependencies:（任意）このタスクが依存する他のタスクとその理由、および必要なアウトカムをリスト化してください。
  dependency_task_sequence_number: 依存するタスクの番号(task_sequence_number)
  reason: 理由
  required_outcome_desired_information_uids: このタスクを実行するために必要なdesired_informationのuid
  required_outcome_desired_robot_state_uids: このタスクを実行するために必要なrobot_stateのuid
task_environmental_conditions:（任意）タスクを実行するために必要な条件を記述してください（物理的条件と情報条件）。
  "required_physical_conditions":（任意）物理的条件
  "required_information_conditions":（任意）情報条件
    "required_information_locations":（任意）必要となる場所の情報
    "required_information_objects":（任意）必要となるオブジェクトの情報 
task_reason:（必須）このタスクを行う理由を記述してください。
task_outcome:（必須）タスクの完了条件を明示してください。以下の2つの情報を含めます：
  desired_information:（任意） このタスクで得られるべき情報。
  desired_robot_state:（任意）タスク完了時にロボットが持つべき状態（必ず以下の候補一覧からのみ選択すること、該当しない場合は選択しない）。

desired_robot_state の候補一覧（これ以外の候補は選択しないこと）:
{{state_descriptions}}

出力は以下のJSONフォーマットで記述してください：

{
  "tasks": [
    {
      "task_sequence_number": "int",
      "task_description": "string",
      "task_additional_info": "string",
      "task_dependencies": [
        {
          "dependency_task_sequence_number": "int",
          "reason": "string",
          "required_outcome_desired_information_uids": ["int"],
          "required_outcome_desired_robot_state_uids": ["int"]
        }
      ],
      "task_environmental_conditions": {
        "required_physical_conditions": ["string"],
        "required_information_conditions": {
          "required_information_locations": ["string"],
          "required_information_objects": ["string"]
        }
      },
      "task_reason": "string",
      "task_outcome": {
        "desired_information": [
          {
            "uid": "int",
            "description": "string"
          }
        ],
        "desired_robot_state": [
          {
            "uid": "int",
            "state_name": "string",
            "state_args": [
                args1, args2, ...
            ]
          }
        ]
      }
    }
  ]
}
"""