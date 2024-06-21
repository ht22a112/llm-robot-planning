from knowledge.knowledge_base import KnowledgeBase

class ObjectLocationKnowledge(KnowledgeBase):
    def __init__(self):
        super().__init__(
            name="オブジェクトの位置情報"
        )
    
    def get_info(self) -> list[str]:
        return ["りんご", "バナナ", "机"]
    
class PlaceLocationKnowledge(KnowledgeBase):
    def __init__(self):
        super().__init__(
            name="場所の位置情報"
        )
    
    def get_info(self) -> list[str]:
        return ["キッチン", "玄関", "リビングルーム"]