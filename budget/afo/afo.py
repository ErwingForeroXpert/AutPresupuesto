#  -*- coding: utf-8 -*-
#    Created on 07/01/2022 15:51:23
#    @author: ErwingForero
#
from typing import Any
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
            
        if self.actual_process != process:
            self.actual_process = process
            self.properties_process = AFO_PROCESSES[self.actual_process].get_properties()[self._type] # afo properties for this process
        
        return self.properties_process

    def execute_formulas(self, driver: 'Driver'):

        _drivers, cols_drivers = zip(*driver.get_sub_drivers_for_process(AFO_PROCESSES.FORMULA.value)) #destructuring tuples [(driver, cols), ...]
        _properties = self.get_properties_for_process(AFO_PROCESSES.FORMULA.value)

        # Dataframe
        _table = self.table

        _table = dfo.combine_str_columns(
            dataframe=_table, 
            idx_cols=_properties["key_columns"], 
            drop_duplicates=_properties["key_column_name"]
            )
        #search by 'key'
        _res_table = _table.merge(
            _drivers[0][[_properties["key_column_name"], *cols_drivers[0]]], 
            on=_properties["key_column_name"], 
            how='left'
            )

        # only for the sub_categoria to begin with "amarr"
        # amarres filter
        mask_amarr = (
            pd.isna(_res_table[cols_drivers[0]]).all(axis=1) & 
            _res_table['sub_categoria'].str.contains(pat='(?i)amarr')
            )

        if mask_amarr.sum() > 0:
            self.insert_alert(_res_table[mask_amarr])

        # change values
        # the same size or smaller than the columns would be expected
        columns_to_change = _properties["columns_change"]
        for idx, _column in enumerate(columns_to_change):
            mask = pd.isna(_res_table[cols_drivers[0][idx]])
            # if the found value is nan, the one be had will be left
            _res_table.loc[~mask,
                           _column] = _res_table.loc[~mask, cols_drivers[0][idx]]

        # delete columns unnecessary
        _res_table.drop(cols_drivers[0], axis=1, inplace=True)
        _res_table.reset_index(drop=True, inplace=True)

        # add optionals extra columns
        _res_table2 = None
        if "extra_columns" in _properties.keys():
            _res_table2 = _res_table.merge(
                _drivers[1][[_properties["key_merge_extra_columns"], *cols_drivers[1]]], 
                on=_properties["key_merge_extra_columns"], 
                how='left'
                )
            _res_table2[_properties["extra_columns"]] = np.full(
                (len(_res_table2), len(_properties["extra_columns"])) #rows, cols
                , '-') #value to insert

            # add agrupacion and formato columns
            cols_drivers[1] = [*cols_drivers[1], *_properties["extra_columns"]]
        
        _res_table = AFO_TYPES[self._type].extra_formula_process(
            table=_res_table, 
            drivers= _drivers, 
            cols_drivers= cols_drivers, 
            properties= _properties,
            table2=_res_table2)
        
        # insert in alerts if found nan in any column after sector
        mask = pd.isna(dfo.get_from(_res_table, "sector")).any(axis=1)
        if mask.sum() > 0:
            self.insert_alert(_res_table[mask])

        self.table = _res_table

    def execute_agrupation(self):

        _properties = self.get_properties_for_process(AFO_PROCESSES.FORMULA.value)

        return self.table.groupby(_properties["agg_columns"], as_index=False).agg(
                sum_venta_actual=pd.NamedAgg(
                    column="venta_nta_acum_anio_actual", aggfunc=np.sum),
                sum_venta_ppto=pd.NamedAgg(
                    column="ppto_nta_acum_anio_actual", aggfunc=np.sum),
                sum_venta_anterior=pd.NamedAgg(
                    column="venta_nta_acum_anio_anterior", aggfunc=np.sum),
            )
    
    @staticmethod
    def fast_filter(dataframe: 'pd.DataFrame', columns: 'list|str', type: str, value: 'Any') -> 'np.bool':
        if type == "contains":
            return dataframe[columns].str.contains(pat=value)

    @staticmethod
    def process_excel_to_afo():
        return AFO(table=_file, names=const.COLUMNS_AFO["driver"], **kargs)