#  -*- coding: utf-8 -*-
#    Created on 07/01/2022 15:51:23
#    @author: ErwingForero
#
from afo.func import after_process_formulas_directa
from enum import Enum, unique
from utils.constants import AFO_TYPES as CONST_AFO

@unique
class AFO_TYPES(Enum):
    DIRECTA = "directa"
    CALLE = "calle"
    COMPRA = "compra"

    @classmethod
    def exist(cls, value):
        return value in cls._value2member_map_ 
    
    def get_properties(self) -> object:
        """Get properties of AFO

        Returns:
            object: properties of afo's type see constants for more
        """
        return CONST_AFO[self.value]

    def extra_formula_process(self, **kargs):
        return after_process_formulas_directa(type=self.value, **kargs)