class MessageBase:
    def __init__(self, content):
        self.content = content

class UserMessage(MessageBase):
    pass

class AssistantMessage(MessageBase):
    pass

class TaskMessage(MessageBase):
    pass