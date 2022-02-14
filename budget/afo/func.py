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
        mask = table[properties["filter_replace_columns"]["column"]].str.contains(pat=properties["filter_replace_columns"]["pattern"])
        table.loc[mask,list(properties["replace_columns_for"].keys())] = np.full(
            (mask.sum(), 6),list(properties["replace_columns_for"].values()))

        #replace cod_agente_comercial by actual_codigo_ac
        actual_afo.replace_by(
            dataframe_right=drivers[3][cols_drivers[3]],
            type_replace="not_nan",
            left_on='cod_agente_comercial',
            right_on=cols_drivers[3][0],
            right_replacer=cols_drivers[3][1],
            how="left"
        )  

        #replace cod_agente_comercial by cod cliente
        actual_afo.replace_by(
            dataframe_right=drivers[4][cols_drivers[4]],
            type_replace="not_nan",
            left_on='cod_agente_comercial',
            right_on=cols_drivers[4][0], #codigo_cliente
            left_replace=['nombre_ac', 'oficina_venta'],
            right_replacer=cols_drivers[4][1:3], #[nombre_cliente, oficina_ventas_ecom]
            create_columns=True,
            how="left"
        )
        
        #add other columns
        new_column_names = [f"{properties['add_columns_dif']}{_column}" for _column in properties["add_columns"]]
        table[new_column_name] = table2[cols_drivers[1]]

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

        
    return actual_afo.table
