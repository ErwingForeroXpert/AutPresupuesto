#  -*- coding: utf-8 -*-
#    Created on 07/01/2022 15:51:23
#    @author: ErwingForero
#

import os
import numpy as np
import pandas as pd
from typing import Any
from dataframes.dataframe_optimized import DataFrameOptimized as dfo
from utils import constants as const, feature_flags
from afo.afo_types import AFO_TYPES
from afo.afo_processes import AFO_PROCESSES
from afo.driver import Driver


class AFO(dfo):

    def __init__(self, afo_type: str, *args, **kargs) -> None:
        super().__init__(*args, **kargs)
        self._type = afo_type
        self.properties = self.get_properties(self._type)
        self.assigments = []
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
            self.properties_process = AFO_PROCESSES[self.actual_process].get_properties(
            )[AFO_TYPES[self._type].value]  # afo properties for this process

        return self.properties_process

    def load_progress(self, progress: int) -> None:
        pass
        # if progress == 0:
 
        # elif progress == 1:
        
        # elif progress == 1:
        
        # elif progress == 1:

    def process(self, driver: 'Driver'):
        
        if feature_flags.ENVIROMENT == "DEV" and feature_flags.SKIP_AFO_PROCESS < 0:
                self.save_actual_progress(level=0) #save base loaded

        if "formula" in self.properties["processes"] and feature_flags.SKIP_AFO_PROCESS < 1: 
            self.execute_formulas(driver)
            if feature_flags.ENVIROMENT == "DEV":
                self.save_actual_progress(level=1)

        if "assigment" in self.properties["processes"] and feature_flags.SKIP_AFO_PROCESS < 2:  
            type_sales = self.get_properties_for_process(AFO_PROCESSES.ASSIGNMENT.name)["agg_values"].keys()
             #get types of sales, see utils/contants
            self.assigments = [
                self.execute_assignment(
                    agg_base=self.execute_agrupation(), 
                    level=0, 
                    type_sale=_type_sale) for _type_sale in type_sales
                ]
            if feature_flags.ENVIROMENT == "DEV":
                for idx,  assigment in enumerate(self.assigments):
                    self.save_actual_progress(data=assigment, level=2, optional_end=f"_{list(type_sales)[idx]}")

        if "consolidation" in self.properties["processes"]:
            pass
    def drop_if_all_cero(self, columns: 'list|str'):
        """Delete rows with cero in all columns

        Args:
            columns (list): columns to validate
        """
        mask = ~(self.table[columns] == 0).all(axis=1)
        self.delete_rows(mask)
        self.table.reset_index(drop=True, inplace=True)

    def save_actual_progress(self, data: 'pd.DataFrame'=None, level=0, optional_end= ""):
        """Save actual progress to file.

        Args:
            data (pd.Dataframe, optional): data to be saved if is None will be use the table, Defaults to None
        """

        route_file = os.path.join(const.ROOT_DIR, f"files/progress_{level}_{AFO_TYPES[self._type].value}{optional_end}.csv")
        route_file_test = os.path.join(const.ROOT_DIR, f"test/files/progress_{level}_{AFO_TYPES[self._type].value}{optional_end}.ftr")
        route_file_alerts = os.path.join(const.ALERTS_DIR, f"{AFO_TYPES[self._type].value}_alerts.csv")
        
        #save progress in file
        temp_data = self.table if data is None else data

        temp_data.to_csv(route_file, sep=";", index=False, encoding="latin-1")

        #save progress for test 
        temp_data.to_feather(route_file_test)
        
        #delete alerts
        if os.path.exists(route_file_alerts):
            os.remove(route_file_alerts)

    def execute_formulas(self, driver: 'Driver') -> 'Driver':
        """Execute process of the formulas in the driver.

        Args:
            driver (Driver): driver of values
        """
        _drivers, cols_drivers = zip(*driver.get_sub_drivers_for_process(
            AFO_PROCESSES.FORMULA.name))  # destructuring tuples [(driver, cols), ...]
        cols_drivers = list(cols_drivers)  # so that it can be modified
        _properties = self.get_properties_for_process(
            AFO_PROCESSES.FORMULA.name)

        # Dataframe
        self.table = self.combine_str_columns(
            dataframe=self.table,
            columns=_properties["key_columns"],
            name_res=_properties["key_column_name"]
        )

        # search by 'clave'
        self.replace_many_by(
            dataframe_right=_drivers[0][[_properties["key_column_name"], *cols_drivers[0]]],
            on=_properties["key_column_name"],
            columns_left=_properties["columns_change"],
            columns_right=cols_drivers[0],
            type="change",
            type_replace="not_nan"
        ) 

        # only for the sub_categoria to begin with "amarr"
        self.validate_alert(
            mask = (
            pd.isna(self.table[_properties["columns_change"]]).all(axis=1) &
            self.table['sub_categoria'].str.contains(pat='(?i)amarr') # amarres filter
            ),
            description="Para la sub_categoria Amarre* no se encontraron reemplazos en el driver",
            type = self._type,
            exception=True,
            exception_description=f"se generaron alertas para AFO - {self._type}, revisar en \n {const.ALERTS_DIR}"
        )

        # delete columns unnecessary
        self.table.drop([_properties["key_column_name"]], axis=1, inplace=True)
        self.table.reset_index(drop=True, inplace=True)

        #execute individual process
        self.sub_process_formula(
            drivers=_drivers,
            cols_drivers=cols_drivers
        )

        # insert in alerts if found nan in any column ...
        columns_to_validate = self.table if _properties["validate_nan_columns"] == "all" else self.table[_properties["validate_nan_columns"]]
        self.validate_alert(
            mask= pd.isna(columns_to_validate).any(axis=1),
            description=f"No se encontraron valores en el driver, en alguna de las columnas \n {' '.join(columns_to_validate.columns.tolist())}",
            type = self._type,
            exception=True,
            exception_description=f"se generaron alertas para AFO - {self._type}, revisar en \n {const.ALERTS_DIR}"
        ) 

    def sub_process_formula(
        self,
        drivers: 'list', 
        cols_drivers: 'list', 
        ) -> pd.DataFrame:

        """Individual process of afo files.

        Args:
            drivers (list): drivers see afo/driver
            cols_drivers (list): columns of drivers

        Returns:
            pd.DataFrame: table before process afo
        """

        columns = self.table.columns.tolist()
        _properties = self.properties_process

        # add optionals extra columns
        other_table = None
        if "extra_columns" in _properties.keys():

            other_table = self.table.merge(
                drivers[1][[_properties["key_merge_extra_columns"], *cols_drivers[1]]],
                on=_properties["key_merge_extra_columns"], #tipologia
                how='left'
            )
            other_table[_properties["extra_columns"]] = np.full(
                # rows, cols
                (len(other_table), len(_properties["extra_columns"])), '-')  # value to insert

            # add agrupacion and formato columns
            cols_drivers[1] = [*cols_drivers[1], *_properties["extra_columns"]]


        if self._type == AFO_TYPES.DIRECTA.name:

            # replace by formato
            other_table2 = self.table.merge(
                right=drivers[2][[_properties["key_merge_add_columns"], *cols_drivers[2]]], 
                left_on=columns[9], #formato
                right_on=_properties["key_merge_add_columns"], #formato_orig
                how='left',
                suffixes=("_left", "_right")
                )
            
            #delete "formato_left" and "formato_orig"
            other_table2.drop([f"{columns[9]}_left", _properties["key_merge_add_columns"]], axis = 1, inplace = True)
            other_table2.reset_index(drop=True, inplace=True)
            #rename "formato_right" by "formato"
            other_table2.rename(columns={f"{columns[9]}_right":columns[9]}, inplace=True) 

            # change values
            new_column_names = [f"{_properties['add_columns_dif']}{_column}" for _column in _properties["add_columns"]]

            self.replace_many_by(
                dataframe_right=[other_table, other_table2], 
                merge=False,
                mask=self.table[_properties["filter_add_columns"]["column"]].str.contains(pat=_properties["filter_add_columns"]["pattern"]), # for format whitout be assigned
                mask_idx=0,
                columns_left=new_column_names,
                columns_right=cols_drivers[1:3], 
                type="add_news",
                type_replace="mask",
                def_value=np.nan 
            )

        elif self._type == AFO_TYPES.CALLE.name:

            # replace if found "Sin asignar"
            mask = self.table[
                _properties["filter_replace_columns"]["column"]
                ].str.contains(pat=_properties["filter_replace_columns"]["pattern"])

            self.table.loc[mask, list(_properties["replace_columns_for"].keys())] = np.full(
                (mask.sum(), 
                len(_properties["replace_columns_for"].values())), 
                list(_properties["replace_columns_for"].values())
                )

            #replace cod_agente_comercial by actual_codigo_ac
            self.replace_by(
                dataframe_right=drivers[3][cols_drivers[3]],
                type_replace="not_nan",
                left_on=columns[6], #cod_agente_comercial
                right_on=cols_drivers[3][0], #actual_codigo_ac
                right_replacer=cols_drivers[3][1], #cod_ac_reemplazar
                how="left"
            )  

            #replace cod_agente_comercial by cod cliente
            self.replace_by(
                dataframe_right=drivers[4][cols_drivers[4]],
                type_replace="not_nan",
                left_on=columns[6], #cod_agente_comercial
                right_on=cols_drivers[4][0], #codigo_cliente
                left_replace=_properties["new_columns"], #new columns ['nombre_ac', 'oficina_venta']
                right_replacer=cols_drivers[4][1:3], #[nombre_cliente, oficina_ventas_ecom]
                create_columns=True,
                how="left"
            )



            #add other columns
            for idx, _column in enumerate(_properties["add_columns"]):
                new_column_name = f"{_properties['add_columns_dif']}{_column}"
                self.table[new_column_name] = other_table[cols_drivers[1][idx]]

        elif self._type == AFO_TYPES.COMPRA.name:

            #replace table by cod_agente_comercial
            self.replace_by(
                dataframe_right=drivers[3][cols_drivers[3]],
                type_replace="not_nan",
                left_on=columns[2],
                right_on=cols_drivers[3][0],
                right_replacer=cols_drivers[3][1],
                how="left"
            )

            # replace table by cod cliente
            self.replace_by(
                dataframe_right=drivers[4][cols_drivers[4]],
                type_replace="not_nan",
                left_on=columns[2],
                right_on=cols_drivers[4][0],
                left_replace=columns[3],
                right_replacer=cols_drivers[4][1],
                how="left"
            )

            
        return self.table

    def execute_agrupation(self) -> pd.DataFrame:
        """Get Agrupation
            
        Returns:
            pd.DataFrame: result of agrupation
        """
        _properties = self.get_properties_for_process(
            AFO_PROCESSES.FORMULA.name)
        # [{"col_res":[], "column":""},...]
        agg_values = _properties["agg_values"]

        aggregations = {}
        for agg_val in agg_values:
            aggregations[f"{agg_val['col_res']}"] = pd.NamedAgg(
                column=agg_val['column'], aggfunc=np.sum)

        result = self.table.groupby(_properties["agg_columns"], as_index=False).agg(**aggregations)
        return result

    def execute_assignment(self, agg_base: 'pd.DataFrame' = None, level: 'int' = 0, type_sale: 'str' = "actual"):

        _properties = self.get_properties_for_process(
            AFO_PROCESSES.ASSIGNMENT.name)

        #initial columns
        original_columns = agg_base.columns.tolist()

        # see utils/constants - AFO_PROCESSES
        columns_level = _properties['levels'][level]
        # [{"col_res":[], "column":""},...]  see utils/constants - AFO_PROCESSES
        agg_values = _properties['agg_values']

        aggregations = [{
            f"{agg_values[type_sale]['cols_res'][idx]}": pd.NamedAgg(
                column=agg_values[type_sale]['column'], aggfunc=np.sum)
        } for idx in range(len(agg_values[type_sale]['cols_res']))]

        #mask for invalid sector or values equals to cero
        mask_sectors = (agg_base[_properties["filter_sector"]["column"]].str.contains(
            pat=_properties["filter_sector"]["pattern"]) | (agg_base[agg_values[type_sale]['column']] == 0))
        
        # mask for not assignment
        mask_not_assign = agg_base[_properties["filter_assignment"]["column"]].str.contains(
            pat=_properties["filter_assignment"]["pattern"])

        #mask for assign with negative values
        mask_assign_negatives = ((~mask_not_assign) & (agg_base[agg_values[type_sale]['column']] < 0))

        not_assign = agg_base[(~mask_sectors) & mask_not_assign]  # delete invalid sectors and not assigment
        assign = agg_base[(~(mask_sectors | mask_assign_negatives)) & (~mask_not_assign)] # delete invalid sectors or assign negatives and assigment
        assign_negative = agg_base[~(mask_sectors) & mask_assign_negatives] #delete invalid sectors and save assign with negative values
        agg_base = agg_base[~(mask_sectors | mask_assign_negatives)] # delete invalid sectors or assign negatives
        agg_base.reset_index(drop=True, inplace=True)

        # agrupation about "Ventas asignadas positivas"
        total_sales = assign.groupby(
            columns_level, as_index=False).agg(**aggregations[0])

        # agrupation about "Ventas sin asignar negativas"
        total_sales_not_assign = not_assign.groupby(
            columns_level, as_index=False).agg(**aggregations[1])

        #registers ​​that could not be assigned
        assign_with_no_assign = total_sales_not_assign.merge(
            right=total_sales,
            on=columns_level,
            how="left")
        mask_not_found_not_assigned =  ~pd.isna(assign_with_no_assign[agg_values[type_sale]['cols_res'][0]])
        registers_not_merge_assigned = assign_with_no_assign[mask_not_found_not_assigned]

        if mask_not_found_not_assigned.sum() > 0:
            print( 
                f"WARNING: los valores totales no son iguales, numero de filas: {mask_not_found_not_assigned.sum()}, nivel: {level+1}, tipo: {type_sale}, revisar en \n {const.ALERTS_DIR}")
            
            if level >= len(_properties["levels"])-1: 
                exec_desc = f"El ultimo nivel de agrupacion de asignación aun tiene iniciativas sin asignar \n nivel: {level+1} \n tipo: {type_sale}"  
                self.validate_alert(
                    mask=mask_within_assign,
                    description="aun se encuentran diferencias despues de la ultima asignación",
                    type=self._type,
                    exception_description=exec_desc,
                    aux_table=general_base
                )

            #next columns level
            columns_level = _properties['levels'][level+1]

            #agroup by news columns level
            general_base_aux = general_base[mask_within_assign]
            general_base_aux.reset_index(drop=True, inplace=True)
            # result_diff = general_base_aux.groupby(columns_level, as_index=False).agg(**{
            #     f"{agg_values[type_sale]['cols_res'][0]}": pd.NamedAgg(column=total_columns[1], aggfunc=np.sum) #total_venta_*_y
            #     })

            #get the registers of "columns level" with difference in total
            base_of_diff = agg_base.merge(right=general_base_aux, on=columns_level, how="left")

            #only the registers WITH difference in the total
            mask_diff_by_register = ~pd.isna(base_of_diff[agg_values[type_sale]['cols_res'][0]])

            result = self.execute_assignment(
                agg_base=agg_base[mask_diff_by_register][original_columns],
                level=level+1,
                type_sale=type_sale
            ) 

            base_merge = general_base.merge(right=result, on=original_columns, how="left", suffixes=suffixes)
            mask_no_empty_totals = ~pd.isna(base_merge[total_columns[1]])
            general_base.loc[mask_no_empty_totals, agg_values[type_sale]['cols_res'][0]] = base_merge[total_columns[1]]
            general_base.loc[~mask_no_empty_totals, agg_values[type_sale]['cols_res'][0]] = base_merge[total_columns[0]]

            #remove process values
            total_sales_not_assign = total_sales_not_assign[~mask_not_found_not_assigned]
            
        # insert two columns
        general_base = agg_base.merge(
            right=total_sales,
            on=columns_level,
            how="left").merge(
            right=total_sales_not_assign,
            on=columns_level,
            how="left")

        # 0 for empty values
        general_base.loc[pd.isna(general_base[agg_values[type_sale]['cols_res'][0]]), 
                                agg_values[type_sale]['cols_res'][0]] = 0
        mask_within_assign = pd.isna(general_base[agg_values[type_sale]['cols_res'][1]])
        general_base.loc[mask_within_assign, agg_values[type_sale]['cols_res'][1]] = 0

        # omit the cero values in "total_venta_*_asignada"
        mask_cero_total = general_base[agg_values[type_sale]['cols_res'][0]] == 0
        general_base[_properties["add_columns"][0]] = 0  # porc_participacion
        general_base.loc[~mask_cero_total, _properties["add_columns"][0]] = \
            general_base.loc[~mask_cero_total, agg_values[type_sale]['column']] / \
            general_base.loc[~mask_cero_total, agg_values[type_sale]['cols_res'][0]]  # suma_venta_* / total_venta_*_asignada

        # update sum sales
        general_base[agg_values[type_sale]['column']] = general_base[agg_values[type_sale]['column']] + \
            (general_base[_properties["add_columns"][0]] * general_base[agg_values[type_sale]['cols_res'][1]]) # suma_venta + (porc_participacion * total_venta_*_sin_asignar)
 

        # mask of only values assigment
        mask_assing = (~general_base[_properties["filter_assignment"]["column"]].str.contains(
            pat=_properties["filter_assignment"]["pattern"]))
        
        #general base without "sin asignar"
        all_assign = pd.concat((assign_negative[original_columns], general_base[mask_assing][original_columns]), ignore_index=True)
        total_sales_now = all_assign.groupby(
            columns_level, as_index=False).agg(**aggregations[0])

        #get only "sin asignar" and "asignar positivos"
        total_sales_before = agg_base.groupby(columns_level, as_index=False).agg(**aggregations[0])

        # difference between total sales of "suma venta asignada"
        suffixes=('_x', '_y')
        result_diff = total_sales_now.merge(
            right=total_sales_before,
            on=columns_level,
            how="left",
            suffixes=suffixes
        )

        total_columns = [f"{agg_values[type_sale]['cols_res'][0]}{suffix}" for suffix in suffixes]

        #if there was a difference in total
        mask_diff_results = (np.absolute(result_diff[total_columns[0]] - \
                            result_diff[total_columns[1]]) > _properties["permissible_diff_totals"])
        
        if mask_diff_results.sum() > 0:
            pass
        
        mask_assing = (~general_base[_properties["filter_assignment"]["column"]].str.contains(
            pat=_properties["filter_assignment"]["pattern"]))

        return pd.concat((assign_negative[original_columns], general_base[mask_assing][original_columns]), ignore_index=True)

    @staticmethod
    def get_properties(_type: str) -> None:

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
            encoding=_properties["encoding"],
            **kargs)  # permisible https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html
        # arguments or overwrite previous parameters see utils/constants

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
            delimiter=_properties["delimiter"],
            skiprows=_properties["skiprows"][0],
            header=None,
            names=_properties["columns"],
            converters=_properties["converters"],
            encoding=_properties["encoding"],
            **kargs)  # permisible https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
        # arguments or overwrite previous arguments see utils/constants

        return AFO(afo_type=afo_type, table=dto_instance.table)
