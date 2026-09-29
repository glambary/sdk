class ProjectError(Exception):
    message: str

    def __init__(self, message: str | None = None) -> None:
        if not message:
            message = getattr(self, "message", "ProjectError")

        self.message = message

        super().__init__(message)
