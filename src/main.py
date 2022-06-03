#  -*- coding: utf-8 -*-
#    Created on 07/01/2022 15:51:23
#    @author: ErwingForero 
# 

import os
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
from utils import constants as const, index as utils


@decorator_exception_message(title=const.PROCESS_NAME)
async def process_afo_files(app: 'Application'):
    """Main process for AFO files

    Args:
        app (Application): actual instance of application
    """
    _files = app.get_file()
    margin_months = [int(app.inputs["month_init"].get()), int(app.inputs["month_end"].get())]
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

            files_directa = [
                _path for _path in _only_csv if re.match(AFO_TYPES.DIRECTA.get_properties()["regex_name"], _path.strip())]
            files_calle = [
                _path for _path in _only_csv if re.match(AFO_TYPES.CALLE.get_properties()["regex_name"], _path.strip())]
            files_compra = [
                _path for _path in _only_csv if re.match(AFO_TYPES.COMPRA.get_properties()["regex_name"], _path.strip())]
            files_driver = [
                _path for _path in _only_csv if re.match(Driver.get_properties()["regex_name"], _path.strip())]

            if len(files_directa) == 0:
                tk.messagebox.showerror(
                    const.PROCESS_NAME, "No se encontraron archivos de la directa en la carpeta")
            if len(files_calle) == 0:
                tk.messagebox.showerror(
                    const.PROCESS_NAME, "No se encontraron archivos de la calle en la carpeta")
            if len(files_compra) == 0:
                tk.messagebox.showerror(
                    const.PROCESS_NAME, "No se encontraron archivos de la compra en la carpeta")
            if len(files_driver) == 0:
                tk.messagebox.showerror(
                    const.PROCESS_NAME, "No se encontraron archivos de la driver en la carpeta")

            app.update_label(label="lbl_status", label_text="status_project", text="Convirtiendo archivos...")

            with ThreadPoolExecutor(max_workers=4) as executor:
                arguments = [
                            {"paths": files_directa, "afo_type": AFO_TYPES.DIRECTA.name},
                            {"paths": files_calle, "afo_type": AFO_TYPES.CALLE.name},
                            {"paths": files_compra, "afo_type": AFO_TYPES.COMPRA.name}
                        ]

                futures = [loop.run_in_executor(executor, functools.partial(AFO.from_csv, **args)) for args in arguments]
                future_driver = loop.run_in_executor(executor, functools.partial(Driver.from_csv, paths=files_driver))
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
                [_dt_afo_directa, {"driver": _dt_driver, "margin_months": margin_months}],
                [_dt_afo_calle, {"driver": _dt_driver, "margin_months": margin_months}],
                [_dt_afo_compra, {"driver": _dt_driver, "margin_months": margin_months, "aux_afo": _dt_afo_calle}]
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
        tk.messagebox.showinfo(app.root.title(), f"Proceso terminado revise resultados en la ruta: \n {os.path.join(const.ROOT_DIR, 'resultado')}")
    
    
if __name__ == "__main__":
    
    utils.create_necesary_folders(const.ROOT_DIR, ["files", "resultado"])
    utils.create_necesary_folders(os.path.join(const.ROOT_DIR, "files"), ["temp", "alerts"])

    async_loop = asyncio.get_event_loop()

    App = Application(
        title=const.PROCESS_NAME,
        divisions=[2,2],
        size ="450x200"
    )

    App.insert_action("button", "btn_insert_file", process_afo_files, event_loop=async_loop)
    App.run()
    


