
class CustomException(Exception):
    def __init__(self, message:str, status_code:int=400, error_code:str="CUSTOM_ERROR"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code

    def to_dict(self):
        return {
            "message": self.message,
            "status_code": self.status_code,
            "error_code": self.error_code
        }