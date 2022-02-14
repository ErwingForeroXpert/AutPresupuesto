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
            self.properties_process = AFO_PROCESSES[self.actual_process].get_properties(
            )[AFO_TYPES[self._type].value]  # afo properties for this process

        return self.properties_process

    def drop_if_all_cero(self, columns: 'list|str'):
        """Delete rows with cero in all columns

        Args:
            columns (list): columns to validate
        """
        mask = ~(self.table[columns] == 0).all(axis=1)
        self.delete_rows(mask)
        self.table.reset_index(drop=True, inplace=True)

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
        _table = self.table
        _table = self.combine_str_columns(
            dataframe=_table,
            columns=_properties["key_columns"],
            name_res=_properties["key_column_name"]
        )
        # search by 'key'
        _res_table = _table.merge(
            _drivers[0][[_properties["key_column_name"], *cols_drivers[0]]],
            on=_properties["key_column_name"],
            how='left'
        )

        # only for the sub_categoria to begin with "amarr"
        # amarres filter
        self.validate_alert(
            mask= pd.isna(self.table[_properties["validate_nan_columns"]]).any(axis=1),
            description=f"No se encontraron valores en el driver, en alguna de las columnas \n {_properties['validate_nan_columns']}"
        )
        mask_amarr = (
            pd.isna(_res_table[cols_drivers[0]]).all(axis=1) &
            _res_table['sub_categoria'].str.contains(pat='(?i)amarr')
        )

        if mask_amarr.sum() > 0:
            self.insert_alert(
                alert=_res_table[mask_amarr],
                description="Para la sub_categoria Amarre* no se encontraron reemplazos en el driver")

        # change values
        # the same size or smaller than the columns would be expected
        for idx, _column in enumerate(_properties["columns_change"]):
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
                _drivers[1][[_properties["key_merge_extra_columns"],
                             *cols_drivers[1]]],
                on=_properties["key_merge_extra_columns"],
                how='left'

            )
            _res_table2[_properties["extra_columns"]] = np.full(
                # rows, cols
                (len(_res_table2), len(_properties["extra_columns"])), '-')  # value to insert

            # add agrupacion and formato columns
            cols_drivers[1] = [*cols_drivers[1], *_properties["extra_columns"]]

        _res_table = AFO_TYPES[self._type].extra_formula_process(
            actual_afo=self,
            drivers=_drivers,
            cols_drivers=cols_drivers,
            properties=_properties,
            table2=_res_table2
        )

        # insert in alerts if found nan in any column ...
        self.validate_alert(
            mask= pd.isna(self.table[_properties["validate_nan_columns"]]).any(axis=1),
            description=f"No se encontraron valores en el driver, en alguna de las columnas \n {_properties['validate_nan_columns']}"
        )
        self.table = _res_table

        return self

    def sub_process_formula(
        type:str,
        actual_afo: 'AFO', 
        drivers: 'list', 
        cols_drivers: 'list', 
        properties: 'object',
        table2: 'pd.DataFrame' = None,
        ) -> pd.DataFrame:
        """Individual process of afo files.

        Args:
            type (str): type of afo
            table (pd.DataFrame): table of afo type
            drivers (list): drivers see afo/driver
            cols_drivers (list): columns of drivers
            properties (object): properties of afo type
            table2 (pd.DataFrame, optional): util table used for "directa" and "calle" afo type. Defaults to None.

        Returns:
            pd.DataFrame: table before process afo
        """

        columns = actual_afo.table.columns.tolist()
        table = actual_afo.table

        if type == "directa":
            # driver 3 merge with table by formato
            # formato is included in columns
            table3 = table.merge(
                right=drivers[2][cols_drivers[2]], 
                on=columns[9], #formato
                how='left')

            # change values
            mask = table[columns[9]].str.contains(pat='(?i)sin asignar')  # for format whitout be assigned
            
            for idx, _column in enumerate(properties["add_columns"]):
                
                new_column_name = f"{properties['add_columns_dif']}{_column}"
                table[new_column_name] = np.nan #empty column

                #asigned or not asigned
                table.loc[mask,new_column_name] = table2.loc[mask, 
                                            cols_drivers[1][idx]]
                table.loc[~mask, new_column_name] = table3.loc[~mask,
                                            cols_drivers[2][idx]]

        elif type == "calle":
            # replace if found "Sin asignar"
            mask = table[properties["filter_replace_columns"]["column"]].str.contains(pat=properties["filter_replace_columns"]["pattern"])
            table.loc[mask,list(properties["replace_columns_for"].keys())] = np.full(
                (mask.sum(), 6),list(properties["replace_columns_for"].values()))

            #replace cod_agente_comercial by actual_codigo_ac
            actual_afo.replace_by(
                dataframe_right=drivers[3][cols_drivers[3]],
                type_replace="not_nan",
                left_on='cod_agente_comercial',
                right_on=cols_drivers[3][0],
                right_replacer=cols_drivers[3][1],
                how="left"
            )  

            #replace cod_agente_comercial by cod cliente
            actual_afo.replace_by(
                dataframe_right=drivers[4][cols_drivers[4]],
                type_replace="not_nan",
                left_on='cod_agente_comercial',
                right_on=cols_drivers[4][0], #codigo_cliente
                left_replace=['nombre_ac', 'oficina_venta'],
                right_replacer=cols_drivers[4][1:3], #[nombre_cliente, oficina_ventas_ecom]
                create_columns=True,
                how="left"
            )
            
            #add other columns
            new_column_names = [f"{properties['add_columns_dif']}{_column}" for _column in properties["add_columns"]]
            table[new_column_name] = table2[cols_drivers[1]]

        elif type == "compra":

            #replace table by cod_agente_comercial
            actual_afo.replace_by(
                dataframe_right=drivers[3][cols_drivers[3]],
                type_replace="not_nan",
                left_on=columns[2],
                right_on=cols_drivers[3][0],
                right_replacer=cols_drivers[3][1],
                how="left"
            )

            # replace table by cod cliente
            actual_afo.replace_by(
                dataframe_right=drivers[4][cols_drivers[4]],
                type_replace="not_nan",
                left_on=columns[2],
                right_on=cols_drivers[4][0],
                left_replace=columns[3],
                right_replacer=cols_drivers[4][1],
                how="left"
            )

            
        return actual_afo.table

    def execute_agrupation(self) -> pd.DataFrame:
        """Get Agrupation by next values:
            "venta actual"
            "venta ppto"
            "venta anterior"

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

        return self.table.groupby(_properties["agg_columns"], as_index=False).agg(**aggregations)

    def execute_assignment(self, agg_base: 'pd.DataFrame' = None, level: 'int' = 0, type_sale: 'int' = 0):

        _properties = self.get_properties_for_process(
            AFO_PROCESSES.ASSIGNMENT.name)

        # see utils/constants - AFO_PROCESSES
        actual_level = _properties['levels'][level]
        # [{"col_res":[], "column":""},...]  see utils/constants - AFO_PROCESSES
        agg_values = _properties['agg_values']

        # mask for not assignment
        mask_not_assign = agg_base[_properties["filter_assignment"]["column"]].str.contains(
            pat=_properties["filter_assignment"]["pattern"]) & agg_base[agg_values[type_sale]['column']] <= 0

        not_assign = agg_base[mask_not_assign]  # sin asignar menores a 0
        assign = agg_base[~mask_not_assign]

        # agrupation about "Ventas asignadas positivas"
        aggregation = {
            f"{agg_values[type_sale][0]['col_res']}": pd.NamedAgg(
                column=agg_values[type_sale]['column'], aggfunc=np.sum)
        }
        total_sales = assign.groupby(
            actual_level["columns"], as_index=False).agg(**aggregation)

        # agrupation about "Ventas sin asignar negativas"
        aggregation = {
            f"{agg_values[type_sale][1]['col_res']}": pd.NamedAgg(
                column=agg_values[type_sale]['column'], aggfunc=np.sum)
        }
        total_sales_not_assign = not_assign.groupby(
            actual_level["columns"], as_index=False).agg(**aggregation)

        # insert two columns
        general_base = agg_base.merge(
            right=total_sales,
            on=actual_level["columns"],
            how="left").merge(
            right=total_sales_not_assign,
            on=actual_level["columns"],
            how="left")

        # 0 for empty values
        general_base.loc[pd.isna(general_base[agg_values[type_sale]
                                 [0]['col_res']]), agg_values[type_sale][0]['col_res']] = 0
        general_base.loc[pd.isna(general_base[agg_values[type_sale]
                                 [1]['col_res']]), agg_values[type_sale][1]['col_res']] = 0

        # sum level act
        mask_cero_total = general_base[agg_values[type_sale]
                                       [0]['col_res']] == 0
        general_base[actual_level["add_columns"][0]] = 0  # porc_participacion
        general_base.loc[~mask_cero_total, actual_level["add_columns"][0]] = general_base.loc[~mask_cero_total, agg_values[type_sale]['column']] / \
            general_base.loc[~mask_cero_total, agg_values[type_sale][0]
                             ['col_res']]  # suma_venta_act / total_venta_act_asignada

        # update sum sales
        general_base[agg_values[type_sale]['column']] = agg_values[type_sale]['column']+(general_base[actual_level["add_columns"][0]] *
                                                                                         general_base[agg_values[type_sale][1]['col_res']])  # suma_venta + (total_venta_act_sin_asignar * porc_participacion)

        # agrupation by "Ventas actuales positivas"
        total_sales_now = assign.groupby(actual_level["columns"], as_index=False).agg(
            {
                f"{agg_values[type_sale][0]['col_res']}": pd.NamedAgg(
                    column=agg_values[type_sale]['column'], aggfunc=np.sum)
            }
        )

        # difference between total sales of "suma venta"
        mask_diff_results = ~(total_sales[agg_values[type_sale]['column']]
                              == total_sales_now[agg_values[type_sale]['column']])

        if mask_diff_results.sum() > 0:
            print(
                f"WARNING: los valores totales no son iguales, numero de filas: {mask_diff_results.sum()}, nivel: {level}, tipo: {type_sale}")
            diff_totals = total_sales[mask_diff_results]
            diff_results = general_base.merge(
                right=diff_totals[actual_level["columns"]], on=actual_level["columns"], how="left")
            return
        else:
            return general_base

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
            **kargs)  # permisible https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
        # arguments or overwrite previous arguments see utils/constants

        return AFO(afo_type=afo_type, table=dto_instance.table)
