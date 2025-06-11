import unittest
import numpy as np
from pathlib import Path
from moea.energyplan.energyplan_base import EnergyPLANBase
from moea.energyplan.energyplan_splool import EnergyPLANSpool
from moea.energyplan.energyplan110 import EnergyPLAN110


def remove_files(folder: Path):
    for file in folder.glob("*"):
        if file.is_file():
            file.unlink()
        elif file.is_dir():
            remove_files(file)
            file.rmdir()


class TestEnergyPlanBaseClass(unittest.TestCase):

    def setUp(self) -> None:
        self.dummy_path = Path("dummy_path")

    def tearDown(self) -> None:
        remove_files(self.dummy_path)

    def test_initialization(self):
        with self.assertRaises(FileNotFoundError):
            EnergyPLANBase(
                energyplan_data_file="non_existent_file.txt",
                input_names=["dummy_input1", "dummy_input2"]
            )


class TestEnergyPlanSpoolClass(unittest.TestCase):

    def setUp(self) -> None:
        self.dummy_path = Path("dummy_path")

    def tearDown(self) -> None:
        remove_files(self.dummy_path)

    def test_setup(self):
        energyplan_spool = EnergyPLANSpool(
            energyplan_data_file="dummy_path",
            input_names=["dummy_input1", "dummy_input2"]
        )
        energyplan_spool._setup()
        self.assertTrue(energyplan_spool.spool_folder.exists())
        self.assertTrue(energyplan_spool.results_folder.exists())


class TestEnergyPLAN110Class(unittest.TestCase):

    def setUp(self) -> None:
        self.energyplan = EnergyPLAN110(
            energyplan_data_file="CEIS_Complete_Current.txt"
        )

    def test_data_file_exists(self):
        with self.assertRaises(FileNotFoundError):
            EnergyPLAN110(energyplan_data_file="non_existent_file.txt")

    def test_parse_input(self):
        data = self.energyplan._parse_input()
        self.assertIn("EnergyUnit", data)
        self.assertIn("CapacityUnit", data)
        self.assertIn("MonetaryUnit", data)

    def test_dump_input(self):
        data = self.energyplan._parse_input()
        self.energyplan._dump_input(data, 0)
        self.assertTrue((self.energyplan.spool_folder / "input0.txt").exists())

    def test_dump_inputs(self):
        self.energyplan._dump_inputs(x=np.array([[0, 1], [2, 3]]),
                                    input_names=["EnergyUnit", "CapacityUnit"])
        self.assertTrue((self.energyplan.spool_folder / "input1.txt").exists())

    def test_run_energyplan(self):
        self.test_dump_input()
        self.energyplan._run_energyplan(0)

    def test_read_values(self):
        self.test_dump_input()
        self.energyplan._run_energyplan(0)
        results = self.energyplan.read_values(
            "CO2-emission (corrected)",
            "Coal",
            "Total CO2 emission costs",
            ("March", "Wave power")
        )
        self.assertEqual(results.shape, (1, 4))


if __name__ == "__main__":
    unittest.main()
