import unittest
import numpy as np
from pathlib import Path
from moea.energyplan.energyplan_base import EnergyPLANBase
from moea.energyplan.energyplan110 import EnergyPLAN110
from moea.energyplan.energyplan161 import EnergyPLAN161


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
            )


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
        self.energyplan._dump_inputs(
            x=np.array([[0, 1], [2, 3]]),
            input_names=["EnergyUnit", "CapacityUnit"]
        )
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


class TestEnergyPLAN161Class(unittest.TestCase):

    def setUp(self) -> None:
        self.energyplan = EnergyPLAN161(
            energyplan_data_file="CIES_Complete_Current_V161.txt"
        )

    def test_data_file_exists(self):
        with self.assertRaises(FileNotFoundError):
            EnergyPLAN161(energyplan_data_file="non_existent_file.txt")

    def test_parse_input(self):
        data = self.energyplan._parse_input()
        self.assertIn("EnergyUnit", data)
        self.assertIn("CapacityUnit", data)
        self.assertIn("MonetaryUnit", data)

    def test_run_energyplan(self):
        self.energyplan._dump_inputs(
            x=np.array([[5002], [5003]]),
            input_names=["input_RES1_capacity"]
        )
        self.energyplan._run_energyplan_spool(2)

    def test_read_values(self):
        self.energyplan.run([
            {"input_RES1_capacity": 5000 + i**2}
            for i in range(10, 12)
        ])
        with self.assertRaises(ValueError):
            self.energyplan.read_values(
                "Total CO2 emission costs",
            )

        results = self.energyplan.read_values(
            "CO2-emission (corrected)",
            "Fixed operation costs",
            ("March", "PV Electr.")
        )
        print(results)
        self.assertEqual(results.shape, (2, 3))


if __name__ == "__main__":
    unittest.main()
