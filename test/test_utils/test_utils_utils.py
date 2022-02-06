import unittest
import os
import gc
from budget.utils import index
from test.test_fixtures import TEST_FILES_ROUTE

class TestUtilsMethods(unittest.TestCase):

    @classmethod
    def setUp(cls) -> None:
        cls.without_macros_book_route = os.path.join(TEST_FILES_ROUTE, 'book_without_macros.xlsm')
        cls.good_book_route = os.path.join(TEST_FILES_ROUTE, 'good_book.xlsm')

    def test_run_macro_inexistent(self) -> None:
        try:
            index.RunMacro(self.without_macros_book_route, "InexistentMacro")
        except Exception as e:
            pass
    
    def test_run_macro_without_params(self) -> None:
        result = index.RunMacro(self.good_book_route, "TestMacroWithoutParams")
        self.assertEqual(result, None)
    
    def test_run_macro_with_params(self) -> None:
        params = [1,2,3]
        result = index.RunMacro(self.good_book_route, "TestMacroWithParams", params)
        self.assertEqual(result, sum(params))
    
    @classmethod   
    def tearDown(cls) -> None:
        #clear data
        gc.collect()