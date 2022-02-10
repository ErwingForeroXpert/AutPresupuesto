#  -*- coding: utf-8 -*-
#    Created on 07/01/2022 15:51:23
#    @author: ErwingForero
#
from typing import Any
import numpy as np
import pandas as pd
from afo.afo_processes import AFO_PROCESSES
from afo.driver import Driver
from dataframes.dataframe_optimized import DataFrameOptimized as dfo
from utils import constants as const
from afo.afo_types import AFO_TYPES

class AFO(dfo):

    def __init__(self, afo_type: str, *args, **kargs) -> None:
        super().__init__(*args, **kargs)
        self._type = afo_type
        self.properties = self.get_properties(self._type)
        self.actual_process = None
        self.properties_process = None

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
            self.properties_process = AFO_PROCESSES[self.actual_process].get_properties()[AFO_TYPES[self._type].value] # afo properties for this process
        
        return self.properties_process

    def drop_if_all_cero(self, columns: 'list|str'):
        """Delete rows with cero in all columns

        Args:
            columns (list): columns to validate
        """
        mask = ~(self.table[columns] == 0).all(axis=1)
        self.delete_rows(mask)

    def execute_formulas(self, driver: 'Driver') -> 'Driver':
        """Execute process of the formulas in the driver.

        Args:
            driver (Driver): driver of values
        """
        _drivers, cols_drivers = zip(*driver.get_sub_drivers_for_process(AFO_PROCESSES.FORMULA.name)) #destructuring tuples [(driver, cols), ...]
        _properties = self.get_properties_for_process(AFO_PROCESSES.FORMULA.name)
            
        # Dataframe
        _table = self.table

        _table = dfo.combine_str_columns(
            dataframe=_table, 
            columns=_properties["key_columns"], 
            name_res=_properties["key_column_name"]
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
            self.insert_alert(
                alert=_res_table[mask_amarr], 
                description= "Para la sub_categoria Amarre* no se encontraron reemplazos en el driver")

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
            self.insert_alert(
                alert=_res_table[mask],
                description= f"No se encontraron valores en el driver, columnas \n {mask.columns.tolist()}")

        self.table = _res_table
        return self

    def execute_agrupation(self) -> pd.DataFrame:
        """Get Agrupation by next values:
            "venta actual"
            "venta ppto"
            "venta anterior"

        Returns:
            pd.DataFrame: result of agrupation
        """
        _properties = self.get_properties_for_process(AFO_PROCESSES.FORMULA.name)
        agg_values = _properties["agg_values"] #[{"col_res":[], "column":""},...] 

        obj_agg_values = {}
        for agg_val in agg_values:
            obj_agg_values[f"{agg_val['col_res']}"] = pd.NamedAgg(
                    column=agg_val['column'], aggfunc=np.sum)
                
        return self.table.groupby(_properties["agg_columns"], as_index=False).agg(obj_agg_values)   

    def execute_assignment(self, data: 'pd.DataFrame'= None, level: 'int'= 0, type_sale: 'int'=0):

        _properties = self.get_properties_for_process(AFO_PROCESSES.ASSIGNMENT.name)

        if data is not None:
            agg_base = data
        else:
            agg_base = self.execute_agrupation()

        actual_level = _properties['levels'][level] #see utils/constants - AFO_PROCESSES
        agg_values = _properties['agg_values'] #[{"col_res":[], "column":""},...]  see utils/constants - AFO_PROCESSES

        #mask for not assignment
        mask_not_assign = agg_base[_properties["filter_assignment"]["column"]].str.contains(pat=_properties["filter_assignment"]["pattern"]) & agg_base[agg_values[type_sale]['column']] <= 0

        not_assign = agg_base[mask_not_assign] #sin asignar menores a 0
        assign = agg_base[~mask_not_assign] 

        #agrupation about "Ventas asignadas positivas"
        total_sales = assign.groupby(actual_level["columns"], as_index=False).agg(
            {
                f"{agg_values[type_sale][0]['col_res']}":pd.NamedAgg(
                    column=agg_values[type_sale]['column'], aggfunc=np.sum)
            }
        )

        #agrupation about "Ventas sin asignar negativas"
        total_sales_not_assign = not_assign.groupby(actual_level["columns"], as_index=False).agg(
            {
                f"{agg_values[type_sale][1]['col_res']}":pd.NamedAgg(
                    column=agg_values[type_sale]['column'], aggfunc=np.sum)
            }
        )

        #insert two columns 
        general_base = agg_base.merge(
            right=total_sales, 
            on=actual_level["columns"], 
            how="left").merge(
            right=total_sales_not_assign, 
            on=actual_level["columns"], 
            how="left")

        #0 for empty values
        general_base.loc[pd.isna(general_base[agg_values[type_sale][0]['col_res']]), agg_values[type_sale][0]['col_res']] = 0 
        general_base.loc[pd.isna(general_base[agg_values[type_sale][1]['col_res']]), agg_values[type_sale][1]['col_res']] = 0 

        #sum level act
        mask_cero_total = general_base[agg_values[type_sale][0]['col_res']] == 0
        general_base[actual_level["add_columns"][0]] = 0 #porc_participacion
        general_base.loc[~mask_cero_total, actual_level["add_columns"][0]] = general_base.loc[~mask_cero_total, agg_values[type_sale]['column']]/ \
                                                                    general_base.loc[~mask_cero_total, agg_values[type_sale][0]['col_res']] #suma_venta_act / total_venta_act_asignada

        #update sum sales
        general_base[agg_values[type_sale]['column']] = agg_values[type_sale]['column']+(general_base[actual_level["add_columns"][0]]*\
                                            general_base[agg_values[type_sale][1]['col_res']]) #suma_venta + (total_venta_act_sin_asignar * porc_participacion)

        #agrupation by "Ventas actuales positivas"
        total_sales_now = assign.groupby(actual_level["columns"], as_index=False).agg(
            {
                f"{agg_values[type_sale][0]['col_res']}":pd.NamedAgg(
                    column=agg_values[type_sale]['column'], aggfunc=np.sum)
            }
        )

        #difference between total sales of "suma venta"
        mask_diff_results = ~(total_sales[agg_values[type_sale]['column']] == total_sales_now[agg_values[type_sale]['column']])

        if mask_diff_results.sum() > 0:
            print(f"WARNING: los valores totales no son iguales, numero de filas: {mask_diff_results.sum()}, nivel: {level}, tipo: {type_sale}")
            diff_totals = total_sales[mask_diff_results]
            diff_results = general_base.merge(right=diff_totals[actual_level["columns"]], on=actual_level["columns"], how="left")
            return 
        else:
            return general_base
        

    @staticmethod
    def get_properties( _type: str) -> None:

        if not AFO_TYPES.exist(_type):
            raise ValueError(f"Type {_type} not found in AFO_TYPES")

        return AFO_TYPES[_type].get_properties()

    @staticmethod
    def from_excel(path: str, afo_type: str, **kargs) -> 'AFO':
        """Create a afo from an Excel file .

        Args:
            path (str): file route

        Returns:
            AFO: instance of AFO
        """ 
        _properties = AFO.get_properties(afo_type)
        dto_instance = dfo.get_table_excel(
            path=path, 
            sheet=_properties["sheet"], 
            skiprows=_properties["skiprows"], 
            columns=_properties["columns"], 
            converters=_properties["converters"], 
            **kargs)    #permisible https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html 
                        #arguments or overwrite previous parameters see utils/constants 

        return AFO(afo_type=afo_type, table=dto_instance.table)
    
    @staticmethod
    def from_csv(path: str, afo_type: str, **kargs):
        """Create a afo from an Csv file .

        Args:
            path (str): file route

        Returns:
            AFO: instance of AFO
        """ 
        _properties = AFO.get_properties(afo_type)
        dto_instance = dto_instance = dfo.get_table_csv(
            path=path, 
            delimiter= _properties["delimiter"], 
            skiprows= _properties["skiprows"][0], 
            header= None,
            names= _properties["columns"], 
            converters=_properties["converters"],
            **kargs)    #permisible https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
                        #arguments or overwrite previous arguments see utils/constants  

        return AFO(afo_type=afo_type, table=dto_instance.table)