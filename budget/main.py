#  -*- coding: utf-8 -*-
#    Created on 07/01/2022 15:51:23
#    @author: ErwingForero 
# 

import tkinter as tk
import re
from concurrent.futures import ThreadPoolExecutor
from afo.afo_types import AFO_TYPES
from utils import constants as const
from afo.afo import AFO, Driver
from gui.application import Application
from gui.func import decorator_exception_message
from utils import constants as const

@decorator_exception_message(title=const.PROCESS_NAME)
def process_afo_files(get_file: 'Function'):
    """Main process for AFO files

    Args:
        get_file (Function): function that brings the file or folder with the files
    """
    _files = get_file()

    if len(_files) == 1:
        _file = _files[0]
        if "xls" in _file:
            with ThreadPoolExecutor() as executor:

                arguments = [{"path": _file}]*3
                results = executor.map(lambda x: AFO.from_excel(**x), arguments)

                temp_driver = executor.submit(lambda x: Driver.from_excel(**x), {"path": _file})
                _dt_driver = temp_driver.result()

            _dt_afo_directa, _dt_afo_calle, _dt_afo_compra = results

        else:
            tk.messagebox.showerror(
                const.PROCESS_NAME, "No se encontro ningun archivo con extension .xls")
    else:

        _only_csv = [
            _path for _path in _files if "csv" in _path or "txt" in _path]
        if len(_only_csv) < 4:
            tk.messagebox.showerror(
                const.PROCESS_NAME, "No se encontraron los archivos necesarios en la carpeta")

        _file_directa = [
            _path for _path in _only_csv if re.match(AFO_TYPES.DIRECTA.get_properties()["regex_name"], _path.strip())][0]
        _file_calle = [
            _path for _path in _only_csv if re.match(AFO_TYPES.CALLE.get_properties()["regex_name"], _path.strip())][0]
        _file_compra = [
            _path for _path in _only_csv if re.match(AFO_TYPES.COMPRA.get_properties()["regex_name"], _path.strip())][0]
        _file_driver = [
            _path for _path in _only_csv if re.match(Driver.get_properties()["regex_name"], _path.strip())][0]

        if _file_directa is None:
            tk.messagebox.showerror(
                const.PROCESS_NAME, "No se encontraron el archivo directa en la carpeta")
        if _file_calle is None:
            tk.messagebox.showerror(
                const.PROCESS_NAME, "No se encontraron el archivo calle en la carpeta")
        if _file_compra is None:
            tk.messagebox.showerror(
                const.PROCESS_NAME, "No se encontraron el archivo compra en la carpeta")
        if _file_driver is None:
            tk.messagebox.showerror(
                const.PROCESS_NAME, "No se encontraron el archivo driver en la carpeta")

        with ThreadPoolExecutor() as executor:
            arguments = [{"path": _file_directa, "afo_type": AFO_TYPES.DIRECTA.name}
                        #  {"path": _file_calle, "afo_type": AFO_TYPES.CALLE.name},
                        #  {"path": _file_compra, "afo_type": AFO_TYPES.COMPRA.name}
            ]
            results = executor.map(lambda x: AFO.from_csv(**x), arguments)

            temp_driver = executor.submit(lambda x: Driver.from_csv(**x), {"path": _file_driver})
            _dt_driver = temp_driver.result()
        
        # _dt_afo_directa, _dt_afo_calle, _dt_afo_compra = results 
        for result in results:
            _dt_afo_directa = result

    # DIRECTA - 
    _dt_afo_directa.drop_if_all_cero(["venta_nta_acum_anio_actual",
             "ppto_nta_acum_anio_actual", "venta_nta_acum_anio_anterior"])

    # CALLE
    # _dt_afo_calle.drop_if_all_cero(["venta_nta_acum_anio_actual",
    #          "ppto_nta_acum_anio_actual", "venta_nta_acum_anio_anterior"])
    # # COMPRA
    # _dt_afo_compra.drop_if_all_cero(["venta_nta_acum_anio_actual",
    #          "ppto_nta_acum_anio_actual", "venta_nta_acum_anio_anterior"])

    with ThreadPoolExecutor() as executor:
            arguments = [
                [_dt_afo_directa, {"driver": _dt_driver}]
                # [_dt_afo_calle, {"driver": _dt_driver}],
                # [_dt_afo_compra, {"driver": _dt_driver}]
                ]

            results = executor.map(lambda x: x[0].execute_formulas(**x[1]), arguments)
            
    for result in results:
        _dt_afo_directa = result
    _dt_afo_directa, _dt_afo_calle, _dt_afo_compra = results 
    agg_directa = _dt_afo_directa.execute_agrupation()
    agg_calle = _dt_afo_calle.execute_agrupation()
    agg_compra = _dt_afo_compra.execute_agrupation()

    print("hi")

if __name__ == "__main__":
    # process_afo_files([""])
    App = Application(
        title=const.PROCESS_NAME,
        divisions=[2,2],
        size ="300x400"
    )
    process_afo_files(App.get_file())
    App.insert_action("button", "btn_insert_file", process_afo_files, get_file=App.get_file())
    App.run()


    #get AFO file
    


