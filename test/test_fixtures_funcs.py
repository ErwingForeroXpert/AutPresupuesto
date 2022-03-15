import faker 
import os
import pandas as pd
import random
from src.utils import index as utils
from .test_fixtures_const import TEST_FILES_PROGRESS_ROUTE, TEST_FILES_RAW_ROUTE

faker.Faker.seed(random.randint(0,100))
fackerclass = faker.Faker()

def generate_list_str(length: 'tuple(int)', size=10):
    return [fackerclass.pystr(*length)]*size

def compare_tables(tables: 'tuple[pd.DataFrame]') -> bool:
    """Compare two tables 
            Expected same length and same order of values

    Args:
        tables (tuple[pd.DataFrame]): tables to compare

    return:
        bool: if the tables are the same
    """

    columns = (table.columns.tolist() for table in tables)
    diff_length = [len(table) for table in tables]
    diff_columns = utils.get_diff_list(columns)
    
    if len(diff_columns) != 0:
        raise ValueError(f"invalid headers of columns, diff found: {diff_columns}")
    
    if diff_length[0] != diff_length[1]:
        raise ValueError(f"invalid length of columns, length's found: {diff_length}")

    for column in columns[0]:
        mask = tables[0][column] == tables[1][column]
        if mask.sum() != 0:
            return False
    
    return True

def get_test_file(name: 'str') -> 'str':
    """Get route of file in test folder

    Args:
        name (str): name of file

    Raises:
        FileNotFoundError: [description]

    Returns:
        str: route of file
    """
    route = os.path.join(TEST_FILES_PROGRESS_ROUTE, name)
    route_raw = os.path.join(TEST_FILES_RAW_ROUTE, name)
    
    if os.path.exists(route):
        return route
    elif os.path.exists(route_raw):
        return route_raw
    else:
        raise FileNotFoundError(f"File not found, path: {route}")