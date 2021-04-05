from abc import ABC, abstractmethod

class DatabaseDriver(ABC):

    @abstractmethod
    def __init__(self, db_config, config):
        pass

    @abstractmethod
    def insert_data(self, data, fields):
        pass