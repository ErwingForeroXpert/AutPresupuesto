import unittest
import gc
from faker import Faker
import numpy as np
from test.test_fixtures import FakeTable
from src.dataframes import DataFrameOptimized
from src.dataframes import func

def criteriaDeleteRows(dataframe, limit=None):
    validator = {
        "columna1": func.validate_start_with("e"),
    }

    return DataFrameOptimized.make_criteria(dataframe, validator, limit)

class TestDataFrameOptimized(unittest.TestCase):
    """Test for DataFrameOptimized methods.
    """
    @classmethod
    def setUp(cls) -> None:
        """Initialize the class .
        Create Fake table with 3 columns random with 100 rows
        limit is 10
        """
        cls.fake = Faker()
        cls.table = FakeTable.generateFrom({
            "columna1": cls.fake.sentence,
            "columna2": cls.fake.sentence,
            "columna3": cls.fake.sentence
        }, 100)
        cls.limit = 10

    def test_dataframe_from_tuple(self) -> 'DataFrameOptimized':
        """Test that valid dataframe from tuple is an instance of the DataFrameOptimized .

        Returns:
            [DataFrameOptimized]: Dataframe
        """
        _table = DataFrameOptimized.from_tuple(self.table.values, self.table.columns)
        self.assertIsInstance(_table, DataFrameOptimized)

        return _table

    def test_dataframe_make_criteria_with_limit(self) -> None:
        """
        Assert that the criteria has the same size of table
        Assert that the criteria has the correct dtype
        Assert that the table has the sum of the rows that satisfy the limit .
        """
        _table = self.test_dataframe_from_tuple()
        criteria = criteriaDeleteRows(_table.table, self.limit)

        self.assertEqual(len(criteria), len(_table))
        self.assertEqual(criteria.dtype, np.dtype('bool'))
        self.assertLessEqual(np.sum(criteria), self.limit)

    def test_dataframe_make_criteria_without_limit(self) -> None:
        """
        Assert that the criteria has the same size of table
        Assert that the criteria has the correct dtype
        """
        _table = self.test_dataframe_from_tuple()
        criteria = criteriaDeleteRows(_table.table)

        self.assertEqual(len(criteria), len(_table))
        self.assertEqual(criteria.dtype, np.dtype('bool'))  

    def test_dataframe_delete_rows_with_limit(self) -> None:
        """
        Assert that the table has fewer rows than before it was deleted.
        """

        _table = self.test_dataframe_from_tuple()
        self.assertIsInstance(_table, DataFrameOptimized)

        temp_table = _table.table
        _table.delete_rows(~criteriaDeleteRows(_table.table, 10))
        self.assertLessEqual(len(_table.table), len(temp_table))

    def test_dataframe_delete_rows_without_limit(self) -> None:
        """
        Assert that the table has fewer rows than before it was deleted.
        """
        
        _table = self.test_dataframe_from_tuple()
        self.assertIsInstance(_table, DataFrameOptimized)

        temp_table = _table.table
        _table.delete_rows(~criteriaDeleteRows(_table.table))
        self.assertLessEqual(len(_table.table), len(temp_table))

    @classmethod   
    def tearDown(cls) -> None:
        #clear data
        del cls.table
        del cls.fake
        gc.collect()