from abc import abstractmethod
from fastapi import status

class DcException(Exception):

    @abstractmethod
    def get_code(self):
        pass
    
    @abstractmethod
    def get_message(self):
        pass

class FileNotFoundException(DcException):
    
    def __init__(self, message: str=None) -> None:
        self.code = status.HTTP_404_NOT_FOUND
        if not message:
            self.message = "fileid not found in data base"
        else:
            self.message  = message
    
    def get_code(self):
        return self.code
    
    def get_message(self) -> str:
        return self.message
    
    def __str__(self) -> str:
        return self.message
    
class VectoridNotFoundException(DcException):
    
    def __init__(self, message: str=None) -> None:
        self.code = status.HTTP_404_NOT_FOUND
        if not message:
            self.message = "vector id is not vector database"
        else:
            self.message  = message
    
    def get_code(self):
        return self.code
    
    def get_message(self) -> str:
        return self.message
    
    def __str__(self) -> str:
        return self.message
