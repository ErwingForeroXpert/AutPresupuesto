import pandas as pd
import numpy as np

def after_process_formulas_directa(
    type:str,
    table: 'pd.DataFrame', 
    drivers: 'list', 
    cols_drivers: 'list', 
    properties: 'object',
    table2: 'pd.DataFrame' = None,
    ) -> pd.DataFrame:

        if type == "directa":
            # driver 3 merge with table by formato
            # formato is included in columns
            table3 = table.merge(
                right=drivers[2][cols_drivers[2]], 
                on='formato', 
                how='left')

            # change values
            mask = table['formato'].str.contains(
                pat='(?i)sin asignar')  # for format whitout be assigned

            for idx, _column in enumerate(properties["add_columns"]):

                # if column not exist in table
                if _column not in table.columns.tolist():
                    table[_column] = np.nan

                #asigned or not asigned
                table.loc[mask,
                               _column] = table2.loc[mask, cols_drivers[1][idx]]
                table.loc[~mask,
                               _column] = table3.loc[~mask, cols_drivers[2][idx]]

                # replace for "-" NaN values 
                _mask_empty = pd.isna(table[_column])
                table.loc[_mask_empty, _column] = '-'

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
                (len(mask), 6),
                ["T", 
                "Tradicional", 
                "TD", 
                "Tiendas", 
                "TG", 
                "Tienda Mixta"])

            # driver 4 merge with table by cod_agente_comercial
            table3 = table.merge(
                right=drivers[3].table[cols_drivers[3]], 
                left_on='cod_agente_comercial',
                right_on='actual_codigo_ac', 
                how='left')  # formato is included in columns

            mask = pd.isna(table3['cod_ac_reemplazar'])

            # replace not nan by new values
            table.loc[~mask, 'cod_agente_comercial'] = table3.loc[~mask, 'cod_ac_reemplazar']

            # driver 5 merge with table by cod cliente
            table4 = table.merge(
                right=drivers[4][cols_drivers[4]], 
                left_on='cod_agente_comercial',
                right_on='codigo_cliente', how='left')  # formato is included in columns

            # add new two columns "Nombre cliente" and "oficina de ventas"
            table['nombre_ac'] = table4[cols_drivers[4][1]]
            table['oficina_venta'] = table4[cols_drivers[4][2]]

        elif type == "compra":

            # driver 4 merge with table by cod_agente_comercial
            table3 = table.merge(
                right=drivers[3][cols_drivers[3]], 
                left_on='cod_agente',
                right_on='actual_codigo_ac', how='left')  # formato is included in columns

            mask = pd.isna(table3['cod_agente'])

            # replace not nan by new values
            table.loc[~mask, 'cod_agente'] = table3.loc[~mask,'cod_ac_reemplazar']

            # driver 5 merge with table by cod cliente
            table4 = table.merge(
                right=drivers[4].table[cols_drivers[4]], 
                left_on='cod_agente', 
                right_on='codigo_cliente', 
                how='left')

            # new column with "agentes" found
            table['agente'] = table4[cols_drivers[4][1]]
        
        return table