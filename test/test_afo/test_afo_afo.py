import re
import unittest

from afo.afo_processes import AFO_PROCESSES
from afo.afo_types import AFO_TYPES
from afo.afo import AFO
from afo.driver import Driver
from test.test_fixtures import generate_list_str, compare_tables, get_test_file

class TestAFOClass(unittest.TestCase):

    @classmethod
    def setUp(cls) -> None:
        """Initialize the class .
        """

        cls.afo_types = [e.name for e in AFO_TYPES]
        cls.afo_files = ["afo_calle.csv", "afo_compra.csv", "afo_directa.csv"]
        cls.wrong_afo_types = generate_list_str((1,5), size=5)
        cls.wrong_afo_process = generate_list_str((1,5), size=5)
        cls.driver = Driver.from_csv(get_test_file('drivers.csv'))
        cls.instances = []
        cls.afos = []

    def test_afo_load_files_csv(self) -> None:
        for file in self.afo_files:
            _type = re.findall(r"(?>=afo_).*(?=.csv)", file)[0].upper()
            afo = AFO.get_table_csv(get_test_file(file), afo_type=_type)
            self.assertIsInstance(afo, AFO)
            self.afos.append(afo)

    def test_afo_class_initialization(self) -> None:
        for type in self.afo_types:
            instance = AFO(afo_type=type)
            self.assertIsInstance(instance, AFO)
            self.assertEqual(instance.properties, AFO_TYPES[type].get_properties())
            self.instances.append(instance)

    def test_afo_wrong_properties(self) -> None:
        for type in self.wrong_afo_types:
            self.assertRaises(ValueError, AFO.get_properties, type)

    def test_afo_wrong_properties_for_process(self) -> None:
        for process in self.wrong_afo_process:
            self.assertRaises(ValueError, self.instances[0].get_properties_for_process, process)

    def test_afo_load_progress_files(self) -> None:
        levels = [0,1,2]
        for instance in self.instances:
            temp_table = instance.table
            for level in levels:
                instance.load_progress(level)
                self.assertNotEqual(instance.table, temp_table)
                if level == 2:
                    self.assertNotEqual(instance.assigments, [])
    
    def test_execute_formulas(self) -> None:
        if self.afos is None:
            self.test_afo_load_files_csv()

        for afo in self.afos:
            if "formula" in afo.properties["processes"]:
                expected_afo = AFO(afo_type=afo._type)
                expected_afo.load_progress(level=1)
                result_afo = afo.execute_formulas(driver=self.driver)

                self.assertTrue(compare_tables((expected_afo.table, result_afo.table)), msg=f"diff in execute formulas {afo._type}")

    def test_execute_agrupation(self) -> None:
        if self.afos is None:
            self.test_afo_load_files_csv()
        
        for afo in self.afos:
            if "formula" in afo.properties["processes"]:
                expected_afo = AFO(afo_type=afo._type)
                expected_afo.load_progress(level=1)
                expected_agg = expected_afo.execute_agrupation()

                result_afo = afo.execute_formulas(driver=self.driver)
                result_agg = result_afo.execute_agrupation()

                self.assertTrue(compare_tables((expected_agg, result_agg)), msg=f"diff in execute agrupation {afo._type}")
    
    def test_execute_assignment(self) -> None:
        if self.afos is None:
            self.test_afo_load_files_csv()

        for afo in self.afos:
            if "assigment" in afo.properties["processes"]:
                expected_afo = AFO(afo_type=afo._type)
                expected_afo.load_progress(level=2)

                result_afo = afo.execute_formulas(driver=self.driver)
                type_sales = result_afo.get_properties_for_process(AFO_PROCESSES.ASSIGNMENT.name)["agg_values"].keys()
                result_assignment = {
                    f"{_type_sale}": result_afo.execute_assignment(
                        agg_base=result_afo.execute_agrupation(), 
                        level=0, 
                        type_sale=_type_sale) for _type_sale in type_sales
                }

                for _type, assignment in expected_afo.assigments.items():
                    self.assertTrue(compare_tables((assignment, result_assignment[_type])), msg=f"diff in execute assignment {afo._type} - {_type}")

    def test_execute_consolidation(self) -> None:
        if self.afos is None:
            self.test_afo_load_files_csv()

        for afo in self.afos:
            if "consolidation" in afo.properties["processes"]:
                expected_afo = AFO(afo_type=afo._type)
                expected_afo.load_progress(level=3)

                result_afo = afo.execute_formulas(driver=self.driver)
                aux_afo = AFO(afo_type="calle").load_progress(level=1)
                type_sales = result_afo.get_properties_for_process(AFO_PROCESSES.CONSOLIDATION.name)["type_sales"]
                result_afo.execute_consolidation(aux_afo=aux_afo, type_sales=type_sales, driver=self.driver)

                self.assertTrue(compare_tables((expected_afo.base_consolidation, result_afo.base_consolidation)), msg=f"diff in execute consolidation {afo._type}")
                

    @classmethod   
    def tearDown(cls) -> None:
        #clear data
        del cls.afo_types
        del cls.wrong_afo_types 
        del cls.wrong_afo_process
        del cls.instances