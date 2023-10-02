
class LoginFailedException(Exception):
    """An exception while logging in."""
    def __init__(self, message: str) -> None:
        super().__init__(message)