#  -*- coding: utf-8 -*-
#    Created on 07/01/2022 15:51:23
#    @author: ErwingForero
#
from afo.afo_processes import AFO_PROCESSES
from pandas import isna
from dataframes.dataframe_optimized import DataFrameOptimized as dfo
from utils import constants as const


class Driver(dfo):

    def __init__(self, *args, **kargs) -> None:
        super().__init__(*args, **kargs)
        self.properties = self.get_properties()
        self._drivers = None
        self.sep_drivers = "sep"
        self.actual_process = None
        self.sub_drivers_process = None

    def process_subdrivers(self) -> 'list[super()]':
        """Processes driver and split it

        Args:
            driver (dfo): principal driver of values in driver sheet afo
        Returns:
            list[dfo]: list of subdrivers found see utils/constants
        """
        table = self.table
        if table is None:
            raise ValueError("table not found")

        _headers = table.columns.to_list()
        _drivers = []

        actual_columns = []
        for i, _head in enumerate(_headers):
            insert = False
            if self.sep_drivers in _head:
                if actual_columns != []:
                    insert = True
            else:
                actual_columns.append(_head)
                if i == len(_headers)-1:
                    insert = True

            if insert:
                _drivers.append(super().from_tuple(
                    values=table[actual_columns].to_numpy(), 
                    columns=actual_columns))
                _drivers[-1].table = _drivers[-1].table[
                    ~isna(_drivers[-1].table)
                    .all(axis=1)
                    ]
                actual_columns = []

        return _drivers

    @property
    def sub_drivers(self) -> 'list[super()]':
        """List of subdrivers.

        Returns:
            list[dfo]: list of subdrivers
        """
        if self.sub_drivers is None:
            self.sub_drivers = self.process_subdrivers()
        
        return self.sub_drivers

    def get_sub_drivers_for_process(self, process: str) -> list[tuple['super()', list[str]]]:
        """Returns a list of all sub - drivers for the process that are required for the process .

        Args:
            process[str]: Actual process

        Raises:
            ValueError: invalid process

        Returns:
            list[tuple[dfo, list[str]]]: get tuple of subdrivers and head columns
        """

        if not AFO_PROCESSES.exist(process):
            raise ValueError(f"Process {process} not found in AFO_PROCESSES")

        _sub_drivers = self.sub_drivers 

        if self.actual_process == process:
            return self.sub_drivers_process
        
        self.actual_process = process
        properties_process_driver = AFO_PROCESSES[self.actual_process].get_properties()["driver"] # driver properties for this process

        index_sub_drivers = properties_process_driver["index_sub_drivers"] #index of each subdriver
        cols_required_sub_drivers = properties_process_driver["cols_required_sub_drivers"] #cols of each subdriver
        subset_index_columns = properties_process_driver["subset_index_columns"] #key for delete duplicates in each subdriver
        drop_duplicates = properties_process_driver["drop_duplicates"] #delete duplicates?
        
        result = []
        for idx_pos, index in enumerate(index_sub_drivers): #iterate index and position to other properties see constanst PROCESSES
            if drop_duplicates[idx_pos]:
                _, res_columns = super().get_header_names_of(_sub_drivers[index].table, cols_required_sub_drivers[idx_pos])
            else:
                _sub_drivers[index].table, res_columns = super().get_header_names_of(_sub_drivers[index].table, cols_required_sub_drivers[idx_pos],
                                                                drop_duplicates=True, subset=subset_index_columns[idx_pos], keep="first", inplace=True)
            result.append((_sub_drivers[index].table, res_columns))
        
        self.sub_drivers_process = result #save actual sub_drivers

        return self.sub_drivers_process
    
    @staticmethod
    def get_properties() -> object:
        """Get the driver properties, see constants for more.

        Returns:
            object: properties defined of the driver
        """
        return const.DRIVER

    @staticmethod
    def from_excel(path: str, **kargs) -> 'Driver':
        """Create a new driver from an Excel file .

        Args:
            path (str): file route

        Returns:
            Driver: instance of driver
        """
        _properties = Driver.get_properties()

        dto_instance = dfo.get_table_excel(
            path=path, 
            sheet=_properties["sheet"], 
            skiprows=_properties["skiprows"], 
            columns=_properties["columns"], 
            converters=_properties["converters"], 
            **kargs)    #permisible https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html 
                        #arguments or overwrite previous parameters see utils/constants 
        return Driver(table=dto_instance.table)
    
    @staticmethod
    def from_csv(path: str, **kargs):
        """Create a new driver from an Csv file .

        Args:
            path (str): file route

        Returns:
            Driver: instance of driver
        """
        _properties = Driver.get_properties()

        dto_instance = dfo.get_table_csv(
            path=path, 
            delimiter= _properties["delimiter"], 
            skiprows= _properties["skiprows"][0], 
            names= _properties["columns"], 
            converters=_properties["converters"],
            header= None,
            **kargs)    #permisible https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
                        #arguments or overwrite previous arguments see utils/constants  
        return Driver(table=dto_instance.table)