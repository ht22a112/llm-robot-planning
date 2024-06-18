from flet import *

class LLMRobotPlannerInfoView(UserControl):
    def __init__(self, page: Page, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.page = page
        self.expand = True
        self.info_view = ListView(auto_scroll=True)

        # self.page.add(
        #     ElevatedButton("update", on_click=lambda e: self.update_gui())
        # )
        
    def build(self):
        return Container(
            content=self.info_view
        )

    def append(self, content: str):
        self.info_view.controls.append(
            Text(value=content)
        )
        self.info_view.update()



    
