from abc import abstractmethod

class VectorDBInterface:
    
    @abstractmethod
    def load_vectordb(self):
        pass

    @abstractmethod
    def save_load():
        pass
    
    @abstractmethod
    def add_document():
        pass

    @abstractmethod
    def delete_document():
        pass

    @abstractmethod
    def run_query():
        pass