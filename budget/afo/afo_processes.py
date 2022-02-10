#  -*- coding: utf-8 -*-
#    Created on 07/01/2022 15:51:23
#    @author: ErwingForero
#

from enum import Enum, unique
from utils.constants import PROCESSES


@unique
class AFO_PROCESSES(Enum):
    FORMULA = "formula"
    ASSIGNMENT = "assignment"
    
    @classmethod
    def exist(cls, key):
        return key in cls.__members__ 
    
    def get_properties(self) -> object:
        """Get properties of PROCESS

        Returns:
            object: properties of "processes" see constants for more
        """
        return PROCESSES[self.value]
