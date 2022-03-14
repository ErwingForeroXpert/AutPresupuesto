import re
import unittest

import pandas as pd
from src.utils import index as utils
from src.afo.driver import Driver
from test.test_fixtures_funcs import generate_list_str, get_test_file

class TestDriverClass(unittest.TestCase):

    @classmethod
    def setUp(cls) -> None:
        """Initialize the class .
        """
        cls.driver = None
        cls.wrong_process = generate_list_str((1,5), size=5)
    
    def test_driver_load_from_csv(self) -> None:
        self.driver = Driver.from_csv(get_test_file("driver.csv"))
        self.assertIsInstance(self.driver, Driver)
        self.assertDictEqual(self.driver.properties, Driver.get_properties())
    
    def test_driver_process_subdrivers(self) -> None:
        sub_drivers = self.driver.process_subdrivers()
        self.assertEqual(utils.is_iterable(sub_drivers))
        for sub_driver in sub_drivers:
            self.assertIsInstance(sub_driver, pd.DataFrame)
    
    def test_driver_wrong_properties_for_process(self) -> None:
        for process in self.wrong_process:
            self.assertRaises(ValueError, self.driver, process)
    
    @classmethod   
    def tearDown(cls) -> None:
        #clear data
        del cls.driver