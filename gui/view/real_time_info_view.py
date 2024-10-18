from flet import *  # type: ignore
from gui.control.selectable_list import SelectableList, SelectableListItem


# ログデータの保存やアクセスは仮の実装（後でちゃんとしたものを実装する）

class LLMRobotPlannerRealTimeInfoView(Container):
    def __init__(self, page: Page, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.page = page
        self.expand = True
        self.list_info_view = SelectableList(auto_scroll=False, on_change=self._on_change_list_item)
        self.left_view = Container(
            content=self.list_info_view,
            expand=True
        )
        self.right_info_view = Container(expand=True)
        
        self.content = Row(
            controls=[self.left_view, VerticalDivider(), self.right_info_view]
        )
        
        # テスト実装
        from typing import Dict
        self.data_logs: Dict[str, dict] = {}
        self.n = 0
    
    # テスト実装
    def append_list_item(
        self, action_text, detail_text, timestamp_text, uid_text, is_instant
    ):
        
        # テスト実装
        log = {"action": action_text, "detail": detail_text, "timestamp": timestamp_text, "uid": uid_text}        
        self.data_logs[uid_text] = log
        
        self.list_info_view.controls.append(
            SelectableListItem(
                on_selected=self._on_list_item_selected,
                on_unselected=self._on_list_item_unselected,
                content=Container(margin=margin.only(left=30*self.n), content=Text(action_text, size=18)),
            )
        )
        self.list_info_view.update()
        if not is_instant:
            self.n += 1
            
    def update_list_item(self, action_text, detail_text, timestamp_text, uid_text, is_duration_end):
        log = {"action": action_text, "detail": detail_text, "timestamp": timestamp_text, "uid": uid_text}        
        self.data_logs[uid_text] = log
        if is_duration_end:
            self.n -= 1
            
    def _on_list_item_selected(self, e):
        e.bgcolor = colors.with_opacity(0.2, colors.WHITE)
        e.update()
        
    def _on_list_item_unselected(self, e):
        e.bgcolor = None
        e.update()
    
    def _on_change_list_item(self, e):
        # テスト実装
        index = e["index"]
        keys = list(self.data_logs.keys())
        log = self.data_logs[keys[index]]
        self._detail_view(log["action"], log["detail"], log["timestamp"], log["uid"])
        
    def _detail_view(self, action_text, detail_text, timestamp_text, uid_text):
        icon_name = icons.ABC
        title_text = action_text
        # detail_text = detail_text
        # timestamp_text = timestamp_text
        # uid_text = uid_text
        
        self.right_info_view.content = Column(
            alignment=MainAxisAlignment.START,
            horizontal_alignment=CrossAxisAlignment.CENTER,
            controls=[
                Container(
                    margin=margin.symmetric(horizontal=10),
                    content=Row(
                        vertical_alignment=CrossAxisAlignment.CENTER,
                        controls=[
                            Icon(
                                name=icon_name,
                                size=48,
                            ),
                            Text(
                                value=title_text,
                                size=24,
                            )
                        ]
                    )
                ),
                Divider(),
                Column(
                    expand=True,
                    spacing=10,
                    controls=[
                        Container(
                            content=Column(
                                controls=[
                                    Text(
                                        value="Detail"
                                    ),
                                    TextField(
                                        value=detail_text,
                                        read_only=True,
                                        max_lines=999,
                                        expand=True,
                                    )
                                ]
                            ),
                            expand=True
                        ),
                        Divider(),
                        Container(
                            content=Column(
                                controls=[
                                    Text(
                                        value="Timestamp"
                                    ),
                                    TextField(
                                        value=timestamp_text,
                                        read_only=True,
                                    )
                                ]
                            )
                        ),
                        Container(
                            content=Column(
                                controls=[
                                    Text(
                                        value="uid"
                                    ),
                                    TextField(
                                        value=uid_text,
                                        read_only=True,
                                    )
                                ]
                            )
                        )
                    ]
                )
            ]
        )
        self.right_info_view.update()
