class ChatEngine:
    def __init__(self, model: str = "gpt-3.5-turbo", temperature: float = 0.7):
        self.model = model
        self.temperature = temperature
