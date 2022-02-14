import pandas as pd
import numpy as np

from afo.afo import AFO

def after_process_formulas_directa(
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
        mask = table['tipologia'].str.contains(pat='(?i)sin asignar')
        table.loc[mask, 
        ["cod_canal", 
        "canal", 
        "cod_sub_canal", 
        "sub_canal", 
        "cod_tipologia", 
        "tipologia"]] = np.full(
            (mask.sum(), 6),
            ["T", 
            "Tradicional", 
            "TD", 
            "Tiendas", 
            "TG", 
            "Tienda Mixta"])

        #replace cod_agente_comercial by actual_codigo_ac
        actual_afo.replace_by(
            dataframe_right=drivers[3][cols_drivers[3]],
            type_replace="not_nan",
            left_on='cod_agente_comercial',
            right_on='actual_codigo_ac',
            right_replacer='cod_ac_reemplazar',
            how="left"
        )

        # driver 5 merge with table by cod cliente
        table4 = table.merge(
            right=drivers[4][cols_drivers[4]], 
            left_on='cod_agente_comercial',
            right_on='codigo_cliente', how='left')  # formato is included in columns

        # add new two columns "Nombre cliente" and "oficina de ventas"
        table['nombre_ac'] = table4[cols_drivers[4][1]]
        table['oficina_venta'] = table4[cols_drivers[4][2]]
        
        #add other columns
        for idx, _column in enumerate(properties["add_columns"]):
            new_column_name = f"{properties['add_columns_dif']}{_column}"
            table[new_column_name] = table2[cols_drivers[1][idx]]

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

        
    return table
