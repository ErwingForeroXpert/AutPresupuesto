#  -*- coding: utf-8 -*-
#    Created on 07/01/2022 15:51:23
#    @author: ErwingForero
#

import os
from sre_compile import isstring
from time import time

from pydantic import ListMinLengthError
from utils import index as utils
from typing import Any
import vaex as vx
import pandas as pd
import numpy as np


class DataFrameOptimized():

    def __init__(self, table=None, **kargs) -> None:
        self.table = None
        self.__alerts = None
        # methods
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

    def insert_alert(self, alert: 'Any', description: str) -> None:
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
            # get only the columns that exist in the alerts
            _required_of_alert = alert[[*_alerts_columns, "description"]]

            self.__alerts = pd.concat(
                [self.__alerts, _required_of_alert], ignore_index=True)

        except Exception as e:
            raise Exception(f"insert_alert {e}")

    def get_alerts(self):
        return self.__alerts

    def validate_alert(self, mask: bool, description: str):

        if mask.sum() > 0:
            self.insert_alert(
                alert=self.table[mask],
                description=description
            )

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

    def replace_by(self, dataframe_right: 'pd.DataFrame', type_replace="all", mask=None, on=None, left_on=None, right_on=None, how="left", left_replace=None, right_replacer=None, create_columns=False, **kargs) -> 'pd.DataFrame':

        if on is None or right_on is None:
            raise ValueError("Required a value key in dataframe_right")

        if mask is None and type_replace not in ["not_nan", "all"]:
            raise ValueError("mask is required")

        _temp_table = self.table.merge(
            right=dataframe_right,
            on=on,
            left_on=left_on,
            right_on=right_on,
            how=how,
            **kargs
        )

        key_right = (
            on if on is not None else right_on) if right_replacer is None else right_replacer
        key_left = (
            on if on is not None else left_on) if left_replace is None else left_replace

        if len(key_left) != len(key_right):
            raise ValueError(
                f"Length of keys invalid, lenght left found {len(key_left)} and right length found {len(key_right)}")

        if create_columns:
            self.table[key_left] = np.nan

        if type_replace == "mask":
            pass
        elif type_replace == "invert_mask":
            mask = ~mask
        elif type_replace == "not_nan":
            mask = ~pd.isna(_temp_table[key_right])
        elif type_replace == "all":
            mask = np.full(len(self.table), True)

        self.table.loc[mask, key_left] = _temp_table.loc[mask, key_right]

        return self.table

    def replace_many_by(self,
                        dataframe_right: 'pd.DataFrame|list', 
                        on=None, 
                        left_on=None, 
                        right_on=None, 
                        how="left",
                        mask=None, 
                        mask_idx=0,
                        columns_right=None, 
                        columns_left=None, 
                        type="change", 
                        type_replace="not_nan", 
                        def_value=np.nan, **kargs):

        if on is None or right_on is None:
            raise ValueError("Required a value key in dataframe_right")

        if len(columns_right) != len(columns_left):
            raise ValueError(
                f"Length of columns invalid, columns right length found {len(columns_right)} and columns left length found {len(columns_left)}")

        if isinstance(dataframe_right, (list, tuple)):
            if len(dataframe_right) > 2:
                raise ListMinLengthError("Invalid size for dataframe_right")

            _temp_table = [
                    self.table.merge(
                    right=dataframe_right[i],
                    on=on,
                    left_on=left_on,
                    right_on=right_on,
                    how=how,
                    **kargs) for i in enumerate(dataframe_right)
            ]
        else:
            _temp_table = self.table.merge(
                right=dataframe_right,
                on=on,
                left_on=left_on,
                right_on=right_on,
                how=how,
                **kargs
            )

        for idx, _column in enumerate(columns_left):

            if type == "add_news" and _column not in self.table.columns.tolist():
                self.table[
                    
                    
                ] = np.full((len(self.table), ), def_value)
            
            if type_replace == "mask":
                pass
            elif type_replace == "not_nan":
                mask = ~pd.isna(_temp_table[mask_idx][columns_right[idx]]) if isinstance(_temp_table, (list, tuple)) else ~pd.isna(_temp_table[columns_right[idx]])
            elif type_replace == "all":
                mask = np.full(len(self.table), True)

            if isinstance(_temp_table, (list, tuple)):
                self.table.loc[mask, _column] = _temp_table[0].loc[mask,
                                                                columns_right[0][idx]]
                self.table.loc[~mask, _column] = _temp_table[1].loc[~mask,
                                                                columns_right[1][idx]]
            else:
                self.table.loc[mask, _column] = _temp_table.loc[mask,
                                                                columns_right[idx]]

        return self.table

    def save_csv(self, folder_path: str, name: str = None, sep=";", **kargs) -> str:
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

        return route

    @staticmethod
    def get_table_excel(path: str, sheet: str, header_idx: 'list' = None, skiprows: 'list' = None, converters: 'list' = None, *args, **kargs) -> 'DataFrameOptimized':
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
            _data = utils.get_data_of_excel_sheet(
                file_path=path, sheet=sheet, header_idx=header_idx, skiprows=skiprows, converters=converters)
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
            if len(values[0]) != len(columns):  # if num of columns not is the same
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
    def get_header_names_of(dataframe: 'pd.DataFrame', idx_cols: list[int], drop_duplicates: bool = False, subset: 'str|list[str]' = None, **kargs) -> tuple[pd.DataFrame, list[str]]:
        _headers = dataframe.columns.tolist()
        _columns_name = [_headers[i] for i in idx_cols]  # get the column names

        if drop_duplicates:
            if subset is None:
                raise ValueError(
                    "subset is required with drop_duplicates true")

            dataframe.drop_duplicates(subset=subset, **kargs)

        return dataframe, _columns_name

    @staticmethod
    def get_from(dataframe: 'pd.DataFrame', start: 'str') -> 'pd.DataFrame':
        cols = dataframe.columns.tolist()
        if start not in cols:
            raise ValueError(f"{start} not found in dataframe")

        return dataframe[cols[cols.index(start):]]

    @staticmethod
    def make_criteria(dataframe: 'DataFrameOptimized', validator: 'dict[str:function]', limit: 'Any' = None) -> 'np.array':
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

        for column, validation in validator.items():  # str, function
            column = column.split(";") if ";" in column else column
            len_column = 1 if isstring(column) else len(column)

            if utils.is_iterable(validation):
                validated = None
                for sub_val in validation:
                    temp_validation = np.apply_along_axis(func1d=sub_val,
                                                          axis=1,
                                                          arr=np.array(
                                                              dataframe[column]).reshape(-1, len_column)
                                                          )
                    validated = temp_validation if validated is None else validated & temp_validation

            else:
                validated = np.apply_along_axis(func1d=validation,
                                                axis=1,
                                                arr=np.array(
                                                    dataframe[column]).reshape(-1, len_column)
                                                )
            mask = validated if mask is None else mask | validated

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
