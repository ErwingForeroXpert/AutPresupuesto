#  -*- coding: utf-8 -*-
#    Created on 07/01/2022 15:51:23
#    @author: ErwingForero
#

from os import getcwd, path
from utils.feature_flags import ENVIROMENT
from dataframes import func

# Project constants
LOG_NAME = "aut_ppto"
PROCESS_NAME = "Proceso Automatización Presupuesto"
ICON_IMAGE = "icon.ico"

AFO_TYPES = {
    "directa": {
        "sheet": "AFO -  Directa",
        "regex_name": r".*directa.*",
        "skiprows": [2, None],
        "delimiter": ";",
        "columns": [
            "cod_oficina",
            "oficina_venta",
            "cod_canal",
            "canal",
            "cod_sub_canal",
            "sub_canal",
            "cod_tipologia",
            "tipologia",
            "agrupacion_clientes",
            "formato",
            "sector",
            "categoria",
            "sub_categoria",
            "linea",
            "marca",
            "mes",
            "venta_nta_acum_anio_actual",
            "ppto_nta_acum_anio_actual",
            "venta_nta_acum_anio_anterior"
        ],
        "converters": {
            "venta_nta_acum_anio_actual": func.mask_price,
            "ppto_nta_acum_anio_actual": func.mask_price,
            "venta_nta_acum_anio_anterior": func.mask_price
        }
    },
    "calle": {
        "sheet": "AFO -  Directa",
        "regex_name": r".*calle.*",
        "skiprows": [2, None],
        "delimiter": ";",
        "columns": [
            "cod_canal",
            "canal",
            "cod_sub_canal",
            "sub_canal",
            "cod_tipologia",
            "tipologia",
            "cod_agente_comercial",
            "sector",
            "categoria",
            "sub_categoria",
            "linea",
            "marca",
            "mes",
            "venta_nta_acum_anio_actual",
            "ppto_nta_acum_anio_actual",
            "venta_nta_acum_anio_anterior"
        ],
        "converters": {
            "venta_nta_acum_anio_actual": func.mask_price,
            "ppto_nta_acum_anio_actual": func.mask_price,
            "venta_nta_acum_anio_anterior": func.mask_price
        }
    },
    "compra": {
        "sheet": "AFO -  Directa",
        "regex_name": r".*compra.*",
        "skiprows": [2, None],
        "delimiter": ";",
        "columns": [
            "cod_oficina",
            "oficina_ventas",
            "cod_agente",
            "agente",
            "cod_canal",
            "canal",
            "cod_sub_canal",
            "sub_canal",
            "cod_tipologia",
            "tipologia",
            "agrupacion",
            "formato",
            "sector",
            "categoria",
            "sub_categoria",
            "linea",
            "marca",
            "mes",
            "venta_nta_acum_anio_actual",
            "ppto_nta_acum_anio_actual",
            "venta_nta_acum_anio_anterior"
        ],
        "converters": {
            "venta_nta_acum_anio_actual": func.mask_price,
            "ppto_nta_acum_anio_actual": func.mask_price,
            "venta_nta_acum_anio_anterior": func.mask_price,
        }
    },
}

DRIVER = {
    "sheet": "Drivers",
    "regex_name": r".*drive.*",
    "skiprows": [1, None],
    "delimiter": ";",
    "columns": [
        "clave",
        "id_consecutivo",
        "sector",
        "vacio1",
        "categoria_producto",
        "vacio2",
        "subcategoria_producto",
        "vacio3",
        "linea_producto",
        "vacio4",
        "marca_producto",
        "vacio5",
        "vacio6",
        "id_consecutivo2",
        "sector2",
        "vacio7",
        "categoria_producto2",
        "vacio8",
        "subcategoria_producto2",
        "vacio9",
        "linea_producto2",
        "vacio10",
        "marca_producto2",
        "vacio11",
        "sep2",
        "sep3",
        "sep4",
        "sep5",
        "sep6",
        "sep7",
        "sep8",
        "sep9",
        "sep10",
        "codigo_tipologia",
        "tipologia",
        "codigo_canal_transformado",
        "canal_transformado",
        "codigo_subcanal_transformado",
        "subcanal_transformado",
        "segmento",
        "segmento_transformado",
        "sep11",
        "sep12",
        "sep13",
        "sep14",
        "formato_orig",
        "canal_transformado2",
        "subcanal_transformado2",
        "segmento2",
        "agrupacion",
        "formato",
        "sep15",
        "sep16",
        "sep17",
        "actual_codigo_ac",
        "cod_ac_reemplazar",
        "sep18",
        "sep19",
        "codigo_cliente",
        "nombre_cliente",
        "oficina_ventas_ecom"
    ],
    "converters": None
}

PROCESSES = {
    "formula": {
        "directa": {
            "key_columns": ["sector", "categoria", "sub_categoria", "linea", "marca"],
            "key_column_name": "clave",
            "columns_change": ['sector', 'categoria', 'sub_categoria', 'linea', 'marca'],
            "extra_columns": ['agrupacion', 'formato'],
            "key_merge_extra_columns": "topologia",
            "add_columns": ['canal', 'sub_canal', 'segmento', 'agrupacion', 'formato'],
            "agg_columns": ["cod_oficina", "oficina_venta",
                            "canal", "sub_canal", "tipologia", "mes",
                            "segmento", "agrupacion", "formato", "sector", "categoria", "sub_categoria", "linea", "marca" "mes"],
            "agg_values":[
                {"col_res":"sum_venta_actual", "column": "venta_nta_acum_anio_actual"}, 
                {"col_res":"sum_venta_ppto", "column": "ppto_nta_acum_anio_actual"},
                {"col_res":"sum_venta_anterior", "column": "venta_nta_acum_anio_anterior"}
                ]
        },
        "calle": {
            "key_columns": ["sector", "categoria", "sub_categoria", "linea", "marca"],
            "key_column_name": "clave",
            "columns_change": ['sector', 'categoria', 'sub_categoria', 'linea', 'marca'],
            "extra_columns": ['agrupacion', 'formato'],
            "key_merge_extra_columns": "topologia",
            "add_columns": ['canal', 'sub_canal', 'segmento', 'agrupacion', 'formato'],
            "agg_columns": ["cod_oficina", "oficina_venta",
                            "canal", "sub_canal", "tipologia", "cod_agente_comercial", "nombre_ac",
                            "sector", "categoria", "sub_categoria", "linea", "marca" "mes"],
            "agg_values":[
                {"col_res":"sum_venta_actual", "column": "venta_nta_acum_anio_actual"}, 
                {"col_res":"sum_venta_ppto", "column": "ppto_nta_acum_anio_actual"},
                {"col_res":"sum_venta_anterior", "column": "venta_nta_acum_anio_anterior"}
                ]
        },
        "compra": {
            "key_columns": ["sector", "categoria", "sub_categoria", "linea", "marca"],
            "key_column_name": "clave",
            "columns_change": ['sector', 'categoria', 'sub_categoria', 'linea', 'marca'],
            "type": "compra",
            "agg_columns": ["oficina_venta",
                            "cod_agente", "sector", "categoria", "sub_categoria",
                            "linea", "marca" "mes"],
            "agg_values":[
                {"col_res":"sum_venta_actual", "column": "venta_nta_acum_anio_actual"}, 
                {"col_res":"sum_venta_ppto", "column": "ppto_nta_acum_anio_actual"},
                {"col_res":"sum_venta_anterior", "column": "venta_nta_acum_anio_anterior"}
                ]
        },
        "driver": {
            # same size and same order in all properties of this object
            "index_sub_drivers": [0, 1, 2, 3, 4],
            "cols_required_sub_drivers": [[15, 17, 19, 21, 23], [3, 5, 7], [1, 2, 3, 4, 5], [0, 1], [0, 1, 2]],
            "subset_index_columns": [None, 'tipologia', 'formato', 'actual_codigo_ac', 'codigo_cliente'],
            "drop_duplicates":[False, True, True, True, True]
        }
    },
    "assignment": {
        "directa": {
            "filter_assignment": {"column": "categoria", "pattern":"(?i)sin asignar"},
            "invalid_sectors": ["helados", "otros no operacional", "otros oper no ccial", "servicios"],
            "agg_values":[
                        {"cols_res":["total_venta_act_asignada", "total_venta_act_sin_asignar"], "column": "sum_venta_actual"},
                        {"cols_res":["total_venta_ant_asignada", "total_venta_ant_sin_asignar"], "column": "sum_venta_anterior"}],
            "add_columns": ["porc_participacion"],
            "levels":[  ["oficina_venta", "segmento", "agrupacion", "formato", "sector", "mes"],
                        ["oficina_venta", "segmento", "agrupacion", "formato", "sector"],
                        ["oficina_venta", "segmento", "sector"]],
        },
    }
}

# routes
PRINCIPAL_FILE_SOURCE = ""
ROOT_DIR = path.abspath(
    path.join(__file__, "../../..")
                        ) if ENVIROMENT == "DEV" else getcwd()
