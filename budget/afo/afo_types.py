#  -*- coding: utf-8 -*-
#    Created on 07/01/2022 15:51:23
#    @author: ErwingForero
#
from enum import Enum, unique
from utils.constants import AFO_TYPES as CONST_AFO

@unique
class AFO_TYPES(Enum):
    DIRECTA = "directa"
    CALLE = "calle"
    COMPRA = "compra"

    @classmethod
    def exist(cls, key):
        return key in cls.__members__ 
    
    def get_properties(self) -> object:
        """Get properties of AFO

        Returns:
            object: properties of afo's type see constants for more
        """
        return CONST_AFO[self.value]