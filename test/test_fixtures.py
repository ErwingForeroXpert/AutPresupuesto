import os
from src.utils import constants as const
from .test_fixtures_funcs import *
from .test_fixtures_const import *

class FakeTable():

    def __init__(self) -> None:
        self.__values = []
        self.__columns = []

    @staticmethod
    def generateFrom(_dict: dict, rows: int = 100) -> 'FakeTable':
        cls = FakeTable()
        cls.setColumns(_dict.keys())

        for _ in range(rows):
            _row = []
            for value in _dict.values():
                _row.append(value())
            cls.setValues(_row)

        return cls

    @property
    def columns(self) -> 'tuple':
        return tuple(self.__columns)

    @property
    def values(self) -> 'tuple':
        return tuple(self.__values)

    def setColumns(self, value) -> None:
        self.__columns = value
    
    def setValues(self, value) -> None:
        self.__values.append(value)