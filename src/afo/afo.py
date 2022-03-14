#  -*- coding: utf-8 -*-
#    Created on 07/01/2022 15:51:23
#    @author: ErwingForero
#

import os
import re
import numpy as np
import pandas as pd
from typing import Any
from dataframes.dataframe_optimized import DataFrameOptimized as dfo
from utils import index as utils, constants as const, feature_flags
from afo.afo_types import AFO_TYPES
from afo.afo_processes import AFO_PROCESSES
from afo.driver import Driver

class AFO(dfo):

    def __init__(self, afo_type: str, *args, **kargs) -> None:
        super().__init__(*args, **kargs)
        self._type = afo_type
        self.properties = self.get_properties(self._type)
        self.assigments = []
        self.base_consolidation = None
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

    def load_progress(self, level: int) -> None: 
        """Load the progress information from the previous files.

        Args:
            level (int): level of actual process to load

        Raises:
            ValueError: if files not exist
        """
        _max_level = min(len(self.properties["processes"]), level)

        files = os.listdir(os.path.join(const.ROOT_DIR, f"test/files/progress/"))
        name_regex = f"progress_{_max_level}_{AFO_TYPES[self._type].value}.*"
        extract_type_regex = fr"(?<=progress_{_max_level}_{AFO_TYPES[self._type].value}_).*(?=.ftr)"

        reg = re.compile(name_regex)
        files_found  = list(filter(reg.match, files))

        if files_found != []:
            if _max_level <= 1 and "formula" in self.properties["processes"]:
                self.table = pd.read_feather(os.path.join(const.ROOT_DIR, f"test/files/progress/{files_found[0]}"))
            elif _max_level == 2:
                self.load_progress(level=1)

                if "assigment" in self.properties["processes"]:
                    names_types_assign = [re.findall(extract_type_regex, filename)[0] for filename in files_found]

                    self.assigments = {
                        f"{names_types_assign[idx]}": pd.read_feather(os.path.join(const.ROOT_DIR, f"test/files/progress/{filename}"))
                        for idx, filename in enumerate(files_found)
                    }   
            elif _max_level == 3 and "consolidation" in self.properties["processes"]:
                self.base_consolidation = pd.read_feather(os.path.join(const.ROOT_DIR, f"test/files/progress/{files_found[0]}"))
        else:
            raise ValueError(f"Files not found, name regex: {name_regex}")

    def process(self, driver: 'Driver', aux_afo: 'AFO'=None):
        
        #load progress
        if feature_flags.ENVIROMENT == "DEV" and feature_flags.SKIP_AFO_PROCESS > -1:
            self.load_progress(level=feature_flags.SKIP_AFO_PROCESS)
        
        if feature_flags.ENVIROMENT == "DEV" and feature_flags.SKIP_AFO_PROCESS < 0:
            self.save_actual_progress(level=0) #save base loaded

        if "formula" in self.properties["processes"] and feature_flags.SKIP_AFO_PROCESS < 1: 
            self.execute_formulas(driver)
            if feature_flags.ENVIROMENT == "DEV":
                self.save_actual_progress(level=1)
            if "formula" == self.properties["processes"][-1]:
                self.save_final(self.execute_agrupation())

        if "assigment" in self.properties["processes"] and feature_flags.SKIP_AFO_PROCESS < 2: 
            type_sales = self.get_properties_for_process(AFO_PROCESSES.ASSIGNMENT.name)["agg_values"].keys()
            #get types of sales, see utils/contants
            self.assigments = {
                f"{_type_sale}": self.execute_assignment(
                    agg_base=self.execute_agrupation(), 
                    level=0, 
                    type_sale=_type_sale) for _type_sale in type_sales
            }
            if feature_flags.ENVIROMENT == "DEV":
                type_sales = list(type_sales)
                for _type,  assigment in self.assigments.items():
                    self.save_actual_progress(data=assigment, level=2, optional_end=f"_{_type}")

            if "assigment" == self.properties["processes"][-1]:
                self.save_final(self.merge_assignment())

        if "consolidation" in self.properties["processes"]:
            type_sales = self.get_properties_for_process(AFO_PROCESSES.CONSOLIDATION.name)["type_sales"]
            self.execute_consolidation(aux_afo=aux_afo, type_sales=type_sales, driver=driver)
            if feature_flags.ENVIROMENT == "DEV":
                self.save_actual_progress(data=self.base_consolidation, level=3)

            self.save_final(self.base_consolidation)
               
    def drop_if_all_cero(self, columns: 'list|str'):
        """Delete rows with cero in all columns

        Args:
            columns (list): columns to validate
        """
        mask = ~(self.table[columns] == 0).all(axis=1)
        self.delete_rows(mask)
        self.table.reset_index(drop=True, inplace=True)

    def save_final(self, data: 'pd.DataFrame'=None):
        route_file = os.path.join(const.ROOT_DIR, f"{AFO_TYPES[self._type].value}.csv")
        #save progress in file
        temp_data = self.table if data is None else data

        temp_data.to_csv(route_file, sep=",", index=False, encoding="latin-1")

    def save_actual_progress(self, data: 'pd.DataFrame'=None, level=0, optional_end= ""):
        """Save actual progress to file.

        Args:
            data (pd.Dataframe, optional): data to be saved if is None will be use the table, Defaults to None
        """

        route_file = os.path.join(const.ROOT_DIR, f"files/temp/progress_{level}_{AFO_TYPES[self._type].value}{optional_end}.csv")
        route_file_test = os.path.join(const.ROOT_DIR, f"test/files/progress/progress_{level}_{AFO_TYPES[self._type].value}{optional_end}.ftr")
        route_file_alerts = os.path.join(const.ALERTS_DIR, f"{AFO_TYPES[self._type].value}_alerts.csv")
        
        #save progress in file
        temp_data = self.table if data is None else data

        temp_data.to_csv(route_file, sep=",", index=False, encoding="latin-1")

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

    def execute_assignment(self, agg_base: 'pd.DataFrame' = None, level: 'int' = 0, type_sale: 'str' = "actual") -> 'pd.DataFrame':

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
        #delete total sales not assign
        total_sales_not_assign = total_sales_not_assign[total_sales_not_assign[agg_values[type_sale]['cols_res'][1]] != 0]

        #registers ​​that could not be assigned
        assign_with_no_assign = total_sales_not_assign.merge(
            right=total_sales,
            on=columns_level,
            how="left")
        mask_not_found_not_assigned =  pd.isna(assign_with_no_assign[agg_values[type_sale]['cols_res'][0]])

        if mask_not_found_not_assigned.sum() > 0:
            print( 
                f"WARNING: los valores totales no son iguales, numero de filas: {mask_not_found_not_assigned.sum()}, nivel: {level+1}, tipo: {type_sale}, afo: {self._type}")
            
            if level >= len(_properties["levels"])-1: 
                exec_desc = f"El ultimo nivel de agrupacion aun tiene iniciativas sin asignar \n nivel: {level+1} \n tipo: {type_sale}"  
                self.validate_alert(
                    mask=mask_not_found_not_assigned,
                    description="aun se encuentran diferencias despues de la ultima asignación",
                    type=self._type,
                    exception_description=exec_desc,
                    aux_table=total_sales_not_assign
                )

         
            #get the registers of "columns level" with not assignation
            base_of_diff = agg_base.merge(right=assign_with_no_assign[mask_not_found_not_assigned], on=columns_level, how="left")

            #only the registers with not posible distribution 
            mask_not_assign_found = pd.isna(base_of_diff[agg_values[type_sale]['cols_res'][1]]) & \
                (base_of_diff[_properties["filter_assignment"]["column"]].str.contains(pat=_properties["filter_assignment"]["pattern"])) #total_venta_*_sin_asignar not found and "sin asignar"

            result = self.execute_assignment(
                agg_base=base_of_diff[~mask_not_assign_found][original_columns],
                level=level+1,
                type_sale=type_sale
            ) 

            #replace by new values
            agg_base = pd.concat((result, base_of_diff[mask_not_assign_found][original_columns]), ignore_index=True)
            #recalculate total sales
            total_sales = result.groupby(
                columns_level, as_index=False).agg(**aggregations[0])
            #remove process values (not necesary recalculate)
            total_sales_not_assign = assign_with_no_assign[~mask_not_found_not_assigned]
            del total_sales_not_assign[agg_values[type_sale]['cols_res'][0]] 

        #end if

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
        general_base.loc[pd.isna(general_base[agg_values[type_sale]['cols_res'][1]]), 
                                agg_values[type_sale]['cols_res'][1]] = 0

        # omit the cero values in "total_venta_*_asignada"
        mask_cero_total = general_base[agg_values[type_sale]['cols_res'][0]] == 0
        general_base[_properties["add_columns"][0]] = 0  # porc_participacion
        general_base.loc[~mask_cero_total, _properties["add_columns"][0]] = \
            general_base.loc[~mask_cero_total, agg_values[type_sale]['column']] / \
            general_base.loc[~mask_cero_total, agg_values[type_sale]['cols_res'][0]]  # suma_venta_* / total_venta_*_asignada

        # update sum sales
        general_base[agg_values[type_sale]['column']] = general_base[agg_values[type_sale]['column']] + \
            (general_base[_properties["add_columns"][0]] * general_base[agg_values[type_sale]['cols_res'][1]]) # suma_venta + (porc_participacion * total_venta_*_sin_asignar)

        mask_assing = (~general_base[_properties["filter_assignment"]["column"]].str.contains(
            pat=_properties["filter_assignment"]["pattern"]))

        return pd.concat((assign_negative[original_columns], general_base[mask_assing][original_columns]), ignore_index=True)
    
    def merge_assignment(self) -> 'pd.DataFrame':
        """Merge list of tables in assignment process

        Returns:
            pd.DataFrame: merge table
        """
        result = None
        _properties = self.get_properties_for_process(AFO_PROCESSES.ASSIGNMENT.name)
        for key, assign in self.assigments.items():
            if result is None:
                result = assign[[*_properties["unique_columns"], _properties["agg_values"][key]["column"]]]
            else:
                result = result.merge(right=assign[[*_properties["unique_columns"], _properties["agg_values"][key]["column"]]], on=_properties["unique_columns"], how="left")

        return result

    def execute_consolidation(self, aux_afo: 'AFO' = None, type_sales: 'list' = None, **kargs) -> 'pd.DataFrame':
        _properties = self.get_properties_for_process(
            AFO_PROCESSES.CONSOLIDATION.name)

        #delete no required columns
        self.assigments["actual"].drop(_properties["no_required_columns"]["actual"], axis = 1, inplace = True) 
        self.assigments["anterior"].drop(_properties["no_required_columns"]["anterior"], axis = 1, inplace = True) 


        base_principal = self.assigments["actual"].merge(
            right=self.assigments["anterior"],
            on=_properties["group_sales_by"],
            how="left"
        )
        mask_nan = self.mask_by(base_principal, {"column": _properties["validate_nan"]}, aux_func=pd.isna)[1]
        base_principal.loc[mask_nan, _properties["validate_nan"]] = 0

        #get aux afo table (calle)
        aux_afo.process(**kargs)
        afo_table = aux_afo.execute_agrupation()

        result = []

        for type_sale in type_sales:
            #properties
            properties_of_sale = _properties[type_sale]
            agg_values = properties_of_sale["agg_values"]
            agg_columns = properties_of_sale["agg_columns"]
            merge_columns = _properties["merge"]

            #agg of sales
            aggregations = []
            for agg_value in agg_values:
                aggregations.append({
                        f"{agg_value['col_res']}": pd.NamedAgg(
                        column=agg_value['column'], aggfunc=np.sum)
                        })

            #replace negatives by 0
            group_table = afo_table.groupby(agg_columns[0], as_index=False).agg(**aggregations[0])
            mask_negatives = self.mask_by(group_table, {"column": agg_values[0]['col_res'], "less": 0})[1]
            group_table.loc[mask_negatives, agg_values[0]['col_res']] = 0

            group_table_total = group_table.groupby(agg_columns[1], as_index=False).agg(**aggregations[1])

            base_merge_final = base_principal.merge( #merge values
                right=group_table,
                left_on=merge_columns["left"],
                right_on=merge_columns["right"],
                how="left"
            )
            #delete different columns in base_merge_final
            base_merge_final.drop(utils.get_diff_list((merge_columns["left"], merge_columns["right"]), _type="right"), axis = 1, inplace = True)

            base_merge_final = base_merge_final.merge( #merge totals
                right=group_table_total,
                left_on=merge_columns["left"],
                right_on=merge_columns["right"],
                how="left"
            )

            #delete different columns in base_merge_final
            base_merge_final.drop(utils.get_diff_list((merge_columns["left"], merge_columns["right"]), _type="right"), axis = 1, inplace = True)

            #mask for "tipologia" not found not found
            mask_not_found = self.mask_by(base_merge_final, {"column": agg_values[0]['col_res']}, aux_func=pd.isna)[1]

            #(sales*value)/sum_value
            base_merge_final.loc[~mask_not_found, _properties['add_column']] = (base_merge_final.loc[~mask_not_found, agg_values[0]['column']]* \
                base_merge_final.loc[~mask_not_found, agg_values[0]['col_res']])/base_merge_final.loc[~mask_not_found, agg_values[1]['col_res']]
            
            #asign sales to "tienda mixta"
            base_merge_final.loc[mask_not_found, _properties["unsold"]["column"]] = _properties["unsold"]["value"]
            base_merge_final.loc[mask_not_found, _properties['add_column']] = base_merge_final.loc[mask_not_found, agg_values[0]["column"]]

            base_merge_final = base_merge_final.groupby(agg_columns[2], as_index=False).agg(**aggregations[2])
            result.append(
                base_merge_final[self.mask_by(base_merge_final, {"column": agg_values[2]['col_res'], "diff": 0})[1]]
            )

        #merge bases
        for base in result:
            validate_column = None if self.base_consolidation is None else \
                utils.get_diff_list((self.base_consolidation.columns.tolist(), base.columns.tolist()), _type="right")
            self.base_consolidation = base if self.base_consolidation is None else \
                self.base_consolidation.merge(base, on=utils.get_diff_list((validate_column , base.columns.tolist()), _type="right"), how="left")
            if utils.is_iterable(validate_column):
                validate_column = validate_column[0]
                mask_zero = self.mask_by(self.base_consolidation, {"column": validate_column, "diff": 0})[1]
                self.base_consolidation.loc[mask_zero, validate_column] = 0

        only_diff = utils.get_diff_list((self.base_consolidation.columns.tolist(), _properties["merge_final"]["found_columns"]), _type="right")
        base_to_merge = aux_afo.table.drop_duplicates(subset=_properties["merge_final"]["found_by"], ignore_index=True)
        
        #use afo_aux with driver
        self.base_consolidation = self.base_consolidation.merge(
            right=base_to_merge[[_properties["merge_final"]["found_by"], *only_diff]],
            on=_properties["merge_final"]["found_by"],
            how="left"
        )


        return self.base_consolidation

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
