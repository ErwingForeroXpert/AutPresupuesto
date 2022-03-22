#  -*- coding: utf-8 -*-
#    Created on 07/01/2022 15:51:23
#    @author: ErwingForero 
# 

import tkinter as tk
import re
import asyncio
import functools

from concurrent.futures import ThreadPoolExecutor

from alive_progress import alive_bar
from afo.afo_types import AFO_TYPES
from utils import constants as const
from afo.afo import AFO, Driver
from gui.application import Application
from gui.func import decorator_exception_message
from utils import constants as const

@decorator_exception_message(title=const.PROCESS_NAME)
async def process_afo_files(app: 'Application'):
    """Main process for AFO files

    Args:
        app (Application): actual instance of application
    """
    _files = app.get_file()
    loop = asyncio.get_running_loop()

    app.update_label(label="lbl_status", label_text="status_project", text="Validando archivos...")

    with alive_bar(4, bar="filling", title="Principal process", calibrate=8) as bar:
        bar.text("leyendo archivos")
        bar()
        if len(_files) == 1:
            _file = _files[0]
            if "xls" in _file:
                with ThreadPoolExecutor(max_workers=4) as executor:

                    arguments = [{"path": _file}]*3

                    futures = [loop.run_in_executor(executor, functools.partial(AFO.from_excel, **args)) for args in arguments]
                    future_driver = loop.run_in_executor(executor, functools.partial(Driver.from_excel, path=_file))
                    results = asyncio.gather([*futures, future_driver])

                _dt_afo_directa, _dt_afo_calle, _dt_afo_compra, _dt_driver = await results

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
                    const.PROCESS_NAME, "No se encontro el archivo directa en la carpeta")
            if _file_calle is None:
                tk.messagebox.showerror(
                    const.PROCESS_NAME, "No se encontro el archivo calle en la carpeta")
            if _file_compra is None:
                tk.messagebox.showerror(
                    const.PROCESS_NAME, "No se encontro el archivo compra en la carpeta")
            if _file_driver is None:
                tk.messagebox.showerror(
                    const.PROCESS_NAME, "No se encontro el archivo driver en la carpeta")

            app.update_label(label="lbl_status", label_text="status_project", text="Convirtiendo archivos...")

            with ThreadPoolExecutor(max_workers=4) as executor:
                arguments = [
                            {"path": _file_directa, "afo_type": AFO_TYPES.DIRECTA.name},
                            {"path": _file_calle, "afo_type": AFO_TYPES.CALLE.name},
                            {"path": _file_compra, "afo_type": AFO_TYPES.COMPRA.name}
                        ]

                futures = [loop.run_in_executor(executor, functools.partial(AFO.from_csv, **args)) for args in arguments]
                future_driver = loop.run_in_executor(executor, functools.partial(Driver.from_csv, path=_file_driver))
                results = asyncio.gather(*futures, future_driver)
            
            _dt_afo_directa, _dt_afo_calle, _dt_afo_compra, _dt_driver = await results


        app.labels_text["status_project"].set("Eliminando ceros de los totales...")
        bar.text("Eliminando ceros de los totales...")
        bar()

        #DIRECTA
        _dt_afo_directa.drop_if_all_cero(["venta_nta_acum_anio_actual",
                "ppto_nta_acum_anio_actual", "venta_nta_acum_anio_anterior"])
        # CALLE
        _dt_afo_calle.drop_if_all_cero(["venta_nta_acum_anio_actual",
                "ppto_nta_acum_anio_actual", "venta_nta_acum_anio_anterior"])
        # COMPRA
        _dt_afo_compra.drop_if_all_cero(["venta_nta_acum_anio_actual",
                "ppto_nta_acum_anio_actual", "venta_nta_acum_anio_anterior"])

        app.labels_text["status_project"].set("Ejecutando proceso principal...\n esto puede tardar vaya tomese un café")
        bar.text("Ejecutando proceso principal...")
        bar()
        with ThreadPoolExecutor(max_workers=4) as executor:
            arguments = [
                [_dt_afo_directa, {"driver": _dt_driver}],
                [_dt_afo_calle, {"driver": _dt_driver}],
                [_dt_afo_compra, {"driver": _dt_driver, "aux_afo": _dt_afo_calle}]
            ]

            futures = [loop.run_in_executor(
                executor, 
                functools.partial(lambda x: x[0].process(**x[1]), args)) 
                for args in arguments
                ]
            results = await asyncio.gather(*futures)

        app.labels_text["status_project"].set("Sin archivos")
        bar.text("Proceso terminado")
        bar()
        tk.messagebox.showinfo(app.root.title(), f"Proceso terminado revise resultados en la ruta: \n {const.ROOT_DIR}")
    
    
if __name__ == "__main__":
    
    async_loop = asyncio.get_event_loop()

    App = Application(
        title=const.PROCESS_NAME,
        divisions=[2,2],
        size ="300x200"
    )

    App.insert_action("button", "btn_insert_file", process_afo_files, event_loop=async_loop)
    App.run()
    


