#  -*- coding: utf-8 -*-
#    Created on 07/01/2022 15:51:23
#    @author: ErwingForero 
# 

import os
from sre_compile import isstring
from time import time
from utils import index as utils
from typing import Any
import vaex as vx
import pandas as pd
import numpy as np

class DataFrameOptimized():

    def __init__(self, table = None, **kargs) -> None:
        self.table = None
        self.__alerts = None
        #methods
        if table is not None:
            self.__process_table(table, **kargs)
            self.create_alerts()

    def __len__(self) -> int:
        return len(self.table) if self.table is not None else 0

    def __process_table(self, table: 'Any', **kargs) -> None:
        """Processes a table from a file or a str - like object .

        Args:
            table (Any): table to be processed

        Raises:
            FileNotFoundError: if table is a path not found
            TypeError: if type is invalid
        """
        if isinstance(table, str):
            if not os.path.exists(table):
                raise FileNotFoundError(f"file not found {table}")
            if "csv" in table or "txt" in table:
                self.table = pd.read_csv(table, **kargs)
            elif "xls" in table:
                self.table = pd.read_excel(table, **kargs)

        elif isinstance(table, (tuple, list)) or type(table).__module__ == np.__name__:
            self.table = pd.DataFrame(table, **kargs)
        elif isinstance(table, (pd.DataFrame)):
            self.table = table
        else:
            raise TypeError(f"Invalid permisible type of {table}")

    def delete_rows(self, criteria: 'np.array') -> 'DataFrameOptimized':
        """Delete rows from the dataframe .
        Args:
            criteria ([numpy.array]): mask of registers, ej: np.alert([True, False, True])

        Raises:
            ValueError: if actual instance hasn't table
            Exception: Generic Exception

        Returns:
            ['DataFrameOptimized']: actual instance of DataFrameOptimized
        """
        try:
            
            if self.table is not None:
                _df = self.table
            else:
                raise ValueError("delete_rows - instance need table")

            self.table = _df[criteria]
            return self

        except Exception as e:
            raise Exception(f"delete_rows {e}")

    def create_alerts(self) -> None:

        if self.table is not None:
            _columns = [*self.table.columns.to_list(), "description"]
            self.__alerts = pd.DataFrame(columns=_columns)
        else:
            raise Exception("Required table of DataFrameOptimized")

    def insert_alert(self, alert: 'Any', description:str) -> None:
        """Inserts an alert into the alert list .

        Args:
            alert ([Any]): Register with alert
            description (str): description of alert
        Raises:
            Exception: Generic Exception 
        """

        try:

            alert["description"] = description
            _alerts_columns = self.table.columns.tolist()
            _required_of_alert = alert[_alerts_columns] #get only the columns that exist in the alerts

            self.__alerts = pd.concat([self.__alerts, _required_of_alert], ignore_index=True)

        except Exception as e:
            raise Exception(f"insert_alert {e}")


    def get_rows(self, criteria: 'np.array') -> 'DataFrameOptimized':
        """Get rows from the dataframe .
        Args:
            criteria ([numpy.array]): mask of registers, ej: np.alert([True, False, True])

        Raises:
            ValueError: if actual instance hasn't table
            Exception: Generic Exception

        Returns:
            ['DataFrameOptimized']: actual instance of DataFrameOptimized
        """
        try:
            
            if self.table is not None:
                _df = self.table
            else:
                raise ValueError("delete_rows - instance need table")

            return _df[criteria]

        except Exception as e:
            raise Exception(f"delete_rows {e}")

    def save_csv(self, folder_path: str, name: str = None, sep=";", **kargs) -> None:
        """Save the table to a CSV file .

        Args:
            folder_path (str): folder
            name (str, optional): name of csv file. Defaults to None.
            sep (str, optional): separator. Defaults to ";".
        """
        if name is None:
            name = f"{time.time()}.csv"

        route = os.path.normpath(os.path.join(folder_path, name))
        self.table.to_csv(path_or_buf=route, sep=sep, **kargs)

    @staticmethod
    def get_table_excel(path: str, sheet: str, header_idx: 'list'= None, skiprows: 'list'= None, converters: 'list' = None, *args, **kargs) -> 'DataFrameOptimized':
        """Returns a DataFrame instance that will be used to parse the table at the given path .

        Args:
            path [str]: path of file
            sheet [str]: sheet of data
            header_idx [list]: list of each starting and ending column, max_len = 2, example: [0,5]
            skiprows [list]: list of each starting and ending row, max_len = 2, example: [0,1000]
            converters [list]: list of columns converters, same size that columns.

        Returns:
            [DataFrameOptimized]: instance of DataFrameOptimized
        """
        try:
            _data = utils.get_data_of_excel_sheet(file_path=path, sheet=sheet, header_idx=header_idx, skiprows=skiprows, converters=converters)
            _dt = DataFrameOptimized(_data, *args, **kargs)
            return _dt
            
        except Exception as e:
            raise Exception(f"get_table_excel - {e}")

    @staticmethod
    def get_table_csv(path: str, *args, **kargs) -> 'DataFrameOptimized':
        """Returns a DataFrame instance that will be used to parse the table at the given path .

        Raises:
            Exception: [description]

        Returns:
            [type]: [description]
        
        Examples
        --------
        DataFrameOptimized.get_table_csv(((1,2), (3,4)), columns=["col1", "col2"])

        DataFrame 
            col1    col2
        0   1       2   
        1   3       4
        """
        try:
            
            _dt = DataFrameOptimized(path, *args, **kargs)
            return _dt
            
        except Exception as e:
            raise Exception(f"get_table_csv - {e}")

    @staticmethod
    def from_tuple(values: tuple, columns: tuple) -> 'Any':
        """Convert a tuple of values and columns to a DataFrameOptimized.

        Raises:
            Exception: if num of columns not is the same

        Returns:
            [vx.DataFrame]: DataFrame
        
        Examples
        --------
        DataFrameOptimized.from_tuple(((1,2), (3,4)), columns=["col1", "col2"])

        DataFrame 
            col1    col2
        0   1       2   
        1   3       4

        """
        try:
            if len(values[0]) != len(columns): #if num of columns not is the same
                raise Exception("values in row are different that columns")
            _dt = DataFrameOptimized(pd.DataFrame(values, columns=columns))
            return _dt
        except Exception as e:
            raise Exception(f"from_tuple - {e}")
    

    @staticmethod
    def combine_str_columns(dataframe: 'pd.DataFrame', columns: list[str], name_res: str) -> 'pd.DataFrame':
        first_column = columns[0]
        other_columns = columns[1:]
        dataframe[name_res] = dataframe[first_column]

        for column in other_columns:
            dataframe[name_res] = dataframe[name_res] + dataframe[column]
        
        return dataframe

    @staticmethod
    def get_header_names_of(dataframe: 'pd.DataFrame', idx_cols: list[int], drop_duplicates: bool, subset: 'str|list[str]', **kargs) -> tuple[pd.DataFrame, list[str]]:
        _headers = dataframe.columns.tolist()
        _columns_name = [_headers[i] for i in idx_cols] #get the column names

        if drop_duplicates:
            if subset is None:
                raise ValueError("subset is required with drop_duplicates true")

            dataframe.drop_duplicates(subset=subset, **kargs) 
        
        return dataframe, _columns_name

    @staticmethod
    def get_from(dataframe: 'pd.DataFrame', start: 'str') -> 'pd.DataFrame':
        cols = dataframe.columns.tolist()
        if start not in cols:
            raise ValueError(f"{start} not found in dataframe")

        return dataframe[cols[cols.index(start):]]
            
    @staticmethod
    def make_criteria(dataframe: 'DataFrameOptimized', validator: 'dict[str:function]', limit:'Any' = None) -> 'np.array':
        """AI is creating summary for make_criteria

        Raises:
            IndexError: Limit more bigger that dataframe

        Returns:
            numpy.Array: mask of values found with validator
        
        Examples
        --------
        dataframe = DataFrameOptimized({
            "column":["first", "second", "estr", "car", "ert", "eft"]
            })
        >>> mask = make_criteria(dataframe, {
            "column": lambda x: str(x).start_with("e")
        })

        array([False, False, True, False, True, True])

        -------
        dataframe = DataFrameOptimized({
            "column":["first", "second", "estr", "car", "ert", "eft"]
            })
        >>> mask = make_criteria(dataframe, {
            "column": lambda x: str(x).start_with("e")
        }, limit = 2)

        array([False, False, True, False, True, False])

        --------
        dataframe = DataFrameOptimized({
            "column1":["first", None, "estr", "car", "ert", "eft"]
            "column2":[1,2,3,4,5,None]
            })

        >>> mask = make_criteria(dataframe, 
        {
            "column1;column2": lambda x: x != None
        })

        array([True, False, True, True, True, False])

        """
        mask = None

        for column, validation in validator.items(): # str, function
            column = column.split(";") if ";" in column else column
            len_column = 1 if isstring(column) else len(column) 

            if utils.is_iterable(validation):
                validated = None
                for sub_val in validation:
                    temp_validation = np.apply_along_axis(func1d=sub_val,  
                                                axis=1, 
                                                arr=np.array(dataframe[column]).reshape(-1,len_column)
                                                )
                    validated = temp_validation  if validated is None else validated & temp_validation
                    
            else:
                validated = np.apply_along_axis(func1d=validation,  
                                                axis=1, 
                                                arr=np.array(dataframe[column]).reshape(-1,len_column)
                                                )
            mask = validated  if mask is None else mask | validated
         
        if limit != None and limit > len(dataframe):
                raise IndexError("make_criteria - limit is more bigger that table")
        elif limit is not None:
            _index = 0
            _iterator = 0
            while _index < limit and _iterator < len(mask):
                if mask[_index] == True:
                    _index += 1
                _iterator += 1
                
            mask[_index + 1:] = False
        
        return mask

