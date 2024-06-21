from flet import *

class LLMRobotPlannerInfoView(UserControl):
    def __init__(self, page: Page, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.page = page
        self.expand = True
        self.left_info_view = Container(content=ListView(auto_scroll=True), expand=True)
        self.right_info_view = Container(content=ListView(auto_scroll=True), expand=True)
        # self.page.add(
        #     ElevatedButton("update", on_click=lambda e: self.update_gui())
        # )
        
    def build(self):
        return Container(
            content=Row(
                controls=[self.left_info_view, VerticalDivider(), self.right_info_view]
            )
        )

    def append_left(self, content: str):
        self.left_info_view.content.controls.append(
            Text(value=content)
        )
        self.left_info_view.update()

    def append_right(self, content: str):
        self.right_info_view.content.controls.append(
            Text(value=content, text_align="end")
        )
        self.right_info_view.update()


    
