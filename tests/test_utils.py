import unittest
import numpy as np
from pathlib import Path

from moea.utils import find_objectives, find_values


class TestIOFunctions(unittest.TestCase):

    def setUp(self) -> None:
        self.test_folder = Path('tests')
        self.results_path = Path('tests/results1.txt')
        return super().setUp()

    def test_get_value(self):
        # Test with a string
        x = find_objectives(self.results_path, 'CO2-emission (total)')
        self.assertEqual(x, 31.575)
        # Test with a tuple for annual values
        x = find_objectives(self.results_path, ('Annual', 'Electr. Demand'))
        self.assertEqual(x, 163.43)
        x = find_objectives(self.results_path, ('Annual', 'PV Electr.'))
        self.assertEqual(x, 34.55)
        # Test with annual minimum
        x = find_objectives(self.results_path,
                            ('Annual Average', 'Electr. Demand'))
        self.assertEqual(x, 18605)

    def test_get_values(self):
        res = find_values(
            self.test_folder,
            'CO2-emission (total)',
            ('Annual', 'Electr. Demand'),
            ('Annual', 'PV Electr.'),
            ('Annual Average', 'Electr. Demand'),
        )
        # With 2 results files in the folder, check that dimension is 2 x 4
        self.assertEqual(res.shape, (2, 4))
        self.assertTrue(
            np.array_equal(res[0], np.array([31.575, 163.43, 34.55, 18605]))
        )
