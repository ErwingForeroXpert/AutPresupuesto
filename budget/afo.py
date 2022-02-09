#  -*- coding: utf-8 -*-
#    Created on 07/01/2022 15:51:23
#    @author: ErwingForero
#

from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
import pandas as pd
import numpy as np
import gc
import re
from dataframes import DataFrameOptimized as dfo
from utils import constants as const
from afo.afo import AFO, Driver

def execute_afo_agrupation(directa: 'dfo', calle: 'dfo', compra: 'dfo') -> 'dfo':
    result = []
    for idx, _type in enumerate([directa, calle, compra]):
        if idx == 0:  # directa
            columns_agg = ["cod_oficina", "oficina_venta",
                           "canal", "sub_canal", "tipologia", "mes",
                           "segmento", "agrupacion"]
        elif idx == 1:  # calle
            columns_agg = ["cod_oficina", "oficina_venta",
                           "canal", "sub_canal", "tipologia", "cod_agente_comercial", "nombre_ac",
                           "sector", "categoria", "sub_categoria", "linea", "marca" "mes"]
        elif idx == 2:  # compra
            columns_agg = ["oficina_venta",
                           "cod_agente", "sector", "categoria", "sub_categoria",
                           "linea", "marca" "mes"]

        result.append(
            _type.table.groupby(columns_agg, as_index=False).agg(
                sum_venta_actual=pd.NamedAgg(
                    column="venta_nta_acum_anio_actual", aggfunc=np.sum),
                sum_venta_ppto=pd.NamedAgg(
                    column="ppto_nta_acum_anio_actual", aggfunc=np.sum),
                sum_venta_anterior=pd.NamedAgg(
                    column="venta_nta_acum_anio_anterior", aggfunc=np.sum),
            )
        )

    return result


def execute_afo_formulas(directa: 'dfo', calle: 'dfo', compra: 'dfo', drivers: list['dfo']) -> 'dfo':
    """Execute formulas for a AFO DIRECTA, CALLE Y COMPRA

    This process first grabs a dataframe and fetches some controller columns,
    then look for the NaN values ​​of the "sub_category" column that starts with "Amarr" and save it in alerts
    then replace the not nan values ​​with the values ​​found in the previous base, and delete innecesary columns,
    finally look for reamining columns in driver and add new columns 'agrupacion', 'formato'

    Returns:
        [list[dfo]]: list of dfo in order [directa, calle, compra]
    """
    means = [{
        "source": directa,
        "key_columns": ["sector", "categoria", "sub_categoria", "linea", "marca"],
        "columns_change": ['sector', 'categoria', 'sub_categoria', 'linea', 'marca'],
        "extra_columns": ['agrupacion', 'formato'],
        "add_columns":['canal', 'sub_canal', 'segmento', 'agrupacion', 'formato'],
        "type": "directa"
    }, {
        "source": calle,
        "key_columns": ["sector", "categoria", "sub_categoria", "linea", "marca"],
        "columns_change": ['sector', 'categoria', 'sub_categoria', 'linea', 'marca'],
        "extra_columns": ['agrupacion', 'formato'],
        "add_columns":['canal', 'sub_canal', 'segmento', 'agrupacion', 'formato'],
        "type": "calle"
    },
        {
        "source": compra,
        "key_columns": ["sector", "categoria", "sub_categoria", "linea", "marca"],
        "columns_change": ['sector', 'categoria', 'sub_categoria', 'linea', 'marca'],
        "type": "compra"
    }
    ]

    result = []

    # get the column names 1, 2, 3 y 4
    _, cols_driver1 = dfo.get_header_names_of(
        drivers[0].table, [15, 17, 19, 21, 23])
    drivers[1].table, cols_driver2 = dfo.get_header_names_of(drivers[1].table, [3, 5, 7],
                                                             drop_duplicates=True, subset=['tipologia'], keep='first', inplace=True)
    drivers[2].table, cols_driver3 = dfo.get_header_names_of(drivers[2].table, [1, 2, 3, 4, 5],
                                                             drop_duplicates=True, subset=['formato'], keep='first', inplace=True)
    drivers[3].table, cols_driver4 = dfo.get_header_names_of(drivers[3].table, [0, 1],
                                                             drop_duplicates=True, subset=['actual_codigo_ac'], keep='first', inplace=True)
    drivers[4].table, cols_driver5 = dfo.get_header_names_of(drivers[4].table, [0, 1, 2],
                                                             drop_duplicates=True, subset=['codigo_cliente'], keep='first', inplace=True)

    for data in means:
        # Dataframe
        _table = data["source"].table

        # explosiones - search by 'clave'
        _table = dfo.combine_str_columns(_table, data["key_columns"], "clave")
        _res_table = _table.merge(drivers[0].table[[
                                  'clave', *cols_driver1]], left_on='clave', right_on='clave', how='left')

        # only for the sub_categoria to begin with "amarr"
        # amarres filter
        mask_amarr = (pd.isna(_res_table[cols_driver1]).all(
            axis=1) & _res_table['sub_categoria'].str.contains(pat='(?i)amarr'))
        if mask_amarr.sum() > 0:
            data["source"].insert_alert(_res_table[mask_amarr])

        # change values
        # the same size or smaller than the columns would be expected
        columns_to_change = data["columns_change"]
        for idx, _column in enumerate(columns_to_change):
            mask = pd.isna(_res_table[cols_driver1[idx]])
            # if the value found is nan, the one be had will be left
            _res_table.loc[~mask,
                           _column] = _res_table.loc[~mask, cols_driver1[idx]]

        # delete columns unnecessary
        _res_table.drop(cols_driver1, axis=1, inplace=True)
        _res_table.reset_index(drop=True, inplace=True)

        # driver 2 merge with table by tipologia

        if data["type"] == "directa" or data["type"] == "calle":
            _res_table2 = _res_table.merge(
                drivers[1].table[['tipologia', *cols_driver2]], on='tipologia', how='left')
            _res_table2[data["extra_columns"]] = np.full(
                (len(_res_table2), len(data["extra_columns"])), '-')
            # add agrupacion and formato columns
            cols_driver2 = [*cols_driver2, *data["extra_columns"]]

        if data["type"] == "directa":

            # driver 3 merge with table by formato
            # formato is included in columns
            _res_table3 = _res_table.merge(
                drivers[2].table[cols_driver3], on='formato', how='left')

            # change values
            mask = _res_table['formato'].str.contains(
                pat='(?i)sin asignar')  # for format whitout be assigned

            for idx, _column in enumerate(data["add_columns"]):

                # if formato column is equals to 'formato'
                if _column not in _res_table.columns.tolist():
                    _res_table[_column] = np.nan

                #asigned or not asigned
                _res_table.loc[mask,
                               _column] = _res_table2.loc[mask, cols_driver2[idx]]
                _res_table.loc[~mask,
                               _column] = _res_table3.loc[~mask, cols_driver3[idx]]
                # for NaN values replace for -
                _mask_empty = pd.isna(_res_table[_column])
                _res_table.loc[_mask_empty, _column] = '-'

        elif data["type"] == "calle":
            # replace if found "Sin asignar"
            mask = _res_table['tipologia'].str.contains(pat='(?i)sin asignar')

            _res_table.loc[mask, ["cod_canal", "canal", "cod_sub_canal", "sub_canal", "cod_tipologia", "tipologia"]] = np.full((len(mask), 6),
                                                                                                                               ["T", "Tradicional", "TD", "Tiendas", "TG", "Tienda Mixta"])

            # driver 4 merge with table by cod_agente_comercial
            _res_table3 = _res_table.merge(drivers[3].table[cols_driver4], left_on='cod_agente_comercial',
                                           right_on='actual_codigo_ac', how='left')  # formato is included in columns
            mask = pd.isna(_res_table3['cod_ac_reemplazar'])

            # replace not nan by new values
            _res_table.loc[~mask, 'cod_agente_comercial'] = _res_table3.loc[~mask,
                                                                            'cod_ac_reemplazar']

            # driver 5 merge with table by cod cliente
            _res_table4 = _res_table.merge(drivers[4].table[cols_driver5], left_on='cod_agente_comercial',
                                           right_on='codigo_cliente', how='left')  # formato is included in columns
            # add new two columns "Nombre cliente" and "oficina de ventas"
            _res_table['nombre_ac'] = _res_table4[cols_driver5[1]]
            _res_table['oficina_venta'] = _res_table4[cols_driver5[2]]

        elif data["type"] == "compra":

            # driver 4 merge with table by cod_agente_comercial
            _res_table3 = _res_table.merge(drivers[3].table[cols_driver4], left_on='cod_agente',
                                           right_on='actual_codigo_ac', how='left')  # formato is included in columns
            mask = pd.isna(_res_table3['cod_agente'])

            # replace not nan by new values
            _res_table.loc[~mask, 'cod_agente'] = _res_table3.loc[~mask,
                                                                  'cod_ac_reemplazar']

            # driver 5 merge with table by cod cliente
            _res_table4 = _res_table.merge(
                drivers[4].table[cols_driver5], left_on='cod_agente', right_on='codigo_cliente', how='left')
            # new column with "agentes" found
            _res_table['agente'] = _res_table4[cols_driver5[1]]

        # insert in alerts if found nan in any column after sector
        mask = pd.isna(dfo.get_from(_res_table, "sector")).any(axis=1)
        if mask.sum() > 0:
            data["source"].insert_alert(_res_table[mask])

        data["source"].table = _res_table
        result.append(data["source"]) 

    return result


def process_afo_driver(driver: 'dfo') -> list['dfo']:
    """Processes a driver and split it

    Args:
        driver (dfo): principal driver of values in driver sheet afo
    Returns:
        list[dfo]: list of subdrivers found see utils/constants
    """
    _table = driver.table
    _headers = _table.columns.to_list()
    _drivers = []

    actual_columns = []
    for i, _head in enumerate(_headers):
        insert = False
        if "sep" in _head:
            if actual_columns != []:
                insert = True
        else:
            actual_columns.append(_head)
            if i == len(_headers)-1:
                insert = True

        if insert:
            _drivers.append(dfo.from_tuple(
                values=_table[actual_columns].to_numpy(), columns=actual_columns))
            _drivers[-1].table = _drivers[-1].table[~pd.isna(
                _drivers[-1].table).all(axis=1)]
            actual_columns = []

    return _drivers


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

                temp_driver = executor.submit(Driver.from_excel, {"path": _file})
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
            _path for _path in _only_csv if re.match(const.AFO_TYPES["directa"]["regex_name"], _path.strip())][0]
        _file_calle = [
            _path for _path in _only_csv if re.match(const.AFO_TYPES["calle"]["regex_name"], _path.strip())][0]
        _file_compra = [
            _path for _path in _only_csv if re.match(const.AFO_TYPES["compra"]["regex_name"], _path.strip())][0]
        _file_driver = [
            _path for _path in _only_csv if re.match(const.DRIVER["regex_name"], _path.strip())][0]

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
            arguments = [{"path": _file_directa},
                         {"path": _file_calle},
                         {"path": _file_compra}
            ]
            results = executor.map(lambda x: AFO.from_csv(**x), arguments)

            temp_driver = executor.submit(Driver.from_csv, {"path": _file_driver})
            _dt_driver = temp_driver.result()

        _dt_afo_directa, _dt_afo_calle, _dt_afo_compra = results 


    # DIRECTA - 
    _dt_afo_directa.dropcero(["venta_nta_acum_anio_actual",
             "ppto_nta_acum_anio_actual", "venta_nta_acum_anio_anterior"])

    # CALLE
    _dt_afo_calle.dropcero(["venta_nta_acum_anio_actual",
             "ppto_nta_acum_anio_actual", "venta_nta_acum_anio_anterior"])
    # COMPRA
    _dt_afo_compra.dropcero(["venta_nta_acum_anio_actual",
             "ppto_nta_acum_anio_actual", "venta_nta_acum_anio_anterior"])

    with ThreadPoolExecutor() as executor:
            arguments = [
                [_dt_afo_directa, {"driver": _dt_driver}],
                [_dt_afo_calle, {"driver": _dt_driver}],
                [_dt_afo_compra, {"driver": _dt_driver}]
                ]

            results = executor.map(lambda x: x[0].execute_formulas(**x[1]), arguments)
            

    _dt_afo_directa, _dt_afo_calle, _dt_afo_compra = results 
    agg_directa = _dt_afo_directa.execute_agrupation()
    agg_calle = _dt_afo_calle.execute_agrupation()
    agg_compra = _dt_afo_compra.execute_agrupation()

    # clean
    gc.collect()
