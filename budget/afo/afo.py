#  -*- coding: utf-8 -*-
#    Created on 07/01/2022 15:51:23
#    @author: ErwingForero
#
import numpy as np
import pandas as pd
from budget.afo.afo_processes import AFO_PROCESSES
from budget.afo.driver import Driver
from dataframes import dataframe_optimized as dfo
from utils import constants as const
from afo.afo_types import AFO_TYPES

class AFO(dfo):

    def __init__(self, afo_type: str, *args, **kargs) -> None:
        super().__init__(*args, **kargs)
        self._type = afo_type
        self.properties = None
        self.actual_process = None
        self.properties_process = None
        self.__process_type()

    def __process_type(self) -> None:

        if not AFO_TYPES.exist(self._type):
            raise ValueError(f"Type {self._type} not found in AFO_TYPES")

        self.properties = AFO_TYPES[self._type].get_properties()

    def get_properties_for_process(self, process: str) -> object:
        """Get properties for AFO process

        Args:
            process[str]: Actual process

        Returns:
            object: properties of afo type for actual process
        """
        if not AFO_PROCESSES.exist(process):
            raise ValueError(f"Process {process} not found in AFO_PROCESSES")
            
        if self.actual_process == process:
            return self.properties_process
        
        self.actual_process = process
        self.properties_process = AFO_PROCESSES[self.actual_process].get_properties()[self._type] # afo properties for this process
        
        return self.properties_process

    def execute_formulas(self, driver: 'Driver'):

        _drivers, cols_driver = zip(*driver.get_sub_drivers_for_process(AFO_PROCESSES.FORMULA.value)) #destructuring tuples [(driver, cols), ...]

        # Dataframe
        _table = self.table

        #search by 'key'
        _table = dfo.combine_str_columns(_table, self.properties["key_columns"], self.properties["key_column_name"])
        _res_table = _table.merge(_drivers[0][[self.properties["key_column_name"], 
                *cols_driver[0]]], on=self.properties["key_column_name"], how='left')

        # only for the sub_categoria to begin with "amarr"
        # amarres filter
        mask_amarr = (pd.isna(_res_table[cols_driver[0]]).all(
            axis=1) & _res_table['sub_categoria'].str.contains(pat='(?i)amarr'))
        if mask_amarr.sum() > 0:
            self.insert_alert(_res_table[mask_amarr])

        # change values
        # the same size or smaller than the columns would be expected
        columns_to_change = data["columns_change"]
        for idx, _column in enumerate(columns_to_change):
            mask = pd.isna(_res_table[cols_driver1[idx]])
            # if the value found is nan, the one be had will be left
            _res_table.loc[~mask,
                           _column] = _res_table.loc[~mask, cols_driver1[idx]]

        # delete columns unnecessary
        _res_table.drop(cols_driver1, axis=1, inplace=True)
        _res_table.reset_index(drop=True, inplace=True)
        
    def execute_agrupation(self):

        columns_agg = self.properties.formula_process.agg_columns # see contants

        return self.table.groupby(columns_agg, as_index=False).agg(
                sum_venta_actual=pd.NamedAgg(
                    column="venta_nta_acum_anio_actual", aggfunc=np.sum),
                sum_venta_ppto=pd.NamedAgg(
                    column="ppto_nta_acum_anio_actual", aggfunc=np.sum),
                sum_venta_anterior=pd.NamedAgg(
                    column="venta_nta_acum_anio_anterior", aggfunc=np.sum),
            )
    

    @staticmethod
    def process_excel_to_afo():
        return AFO(table=_file, names=const.COLUMNS_AFO["driver"], **kargs)