class PromptAgentRequestError(Exception):
    def __init__(self, code: str, message: str | None = None, *, status_code: int = 400):
        self.code = code
        self.message = message or code
        self.status_code = status_code
        super().__init__(self.message)
