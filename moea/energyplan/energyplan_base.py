import subprocess
import numpy as np
from abc import abstractmethod
from pathlib import Path


class EnergyPLANBase:
    """
    Base class for EnergyPLAN models. The class serves as a template for
    specific EnergyPLAN models.

    Parameters
    ----------
    ``energyplan_data_file`` : str or Path
        The name of the EnergyPLAN baseline file.
    """
    energyplan_path = Path()

    def __init__(self,
                 energyplan_data_file: str | Path,
                 ) -> None:
        self.energyplan_data_file = energyplan_data_file
        self.energyplan_exe = self.energyplan_path / "EnergyPLAN.exe"
        self.energyplan_data = self.energyplan_path / \
            f"EnergyPLAN Data/Data/{self.energyplan_data_file}"
        if self.energyplan_path.exists():
            self._setup()
        else:
            raise FileNotFoundError("The EnergyPLAN folder "
                                    f"{self.energyplan_path} does not exists.")

    def _setup(self) -> None:
        self.data = self._parse_input()
        self._setup_spool_folder()
        self._setup_results_folder()

    def _parse_input(self) -> dict:
        """
        Parse the input file of EnergyPLAN and return the data in a dictionary.
        """
        if not self.energyplan_data.exists():
            raise FileNotFoundError(f"{self.energyplan_data} does not exists.")
        with open(self.energyplan_data, 'r', encoding='utf-16') as f:
            rows = f.readlines()
        data = {}
        for i in range(0, len(rows), 2):
            if rows[i] == 'xxx':
                break
            data[rows[i].strip().replace('=', '')] = rows[i + 1].strip()
        return data

    def _setup_spool_folder(self) -> None:
        """
        Check existence and clean the spool folder.
        """
        # Check existence of the spool folder
        self.spool_folder = self.energyplan_path / "spool"
        self.spool_folder.mkdir(parents=True, exist_ok=True)
        # Clean the spool folder
        for file in self.spool_folder.glob('*.txt'):
            file.unlink()

    def _setup_results_folder(self) -> None:
        """
        Check existence and clean the results folder.
        """
        self.results_folder = self.spool_folder / "results"
        # Check existence of the results folder
        self.results_folder.mkdir(parents=True, exist_ok=True)
        # Clean the results folder
        for file in self.results_folder.glob('*.txt'):
            file.unlink()

    def run(self, inputs: list[dict[str, float | str]]) -> None:
        """
        For each individual, overwrite the baseline with the new decision
        variables values and run EnergyPLAN for each of them.
        """
        self._clean_results_folder()
        self._clean_spool_folder()
        for i, values in enumerate(inputs):
            self._dump_input(values, i)
            self._run_energyplan(i)

    def _dump_input(self, values: dict[str, float | str], i: int) -> None:
        """
        Dump the input vector to a file using EnergyPLAN syntax.

        Parameters
        ----------
        ``values`` : dict
            A dict where keys are EnergyPLAN input names and value are the
            values to set.
        ``i`` : int
            An id for the input file to be dumped.
        """
        input_path = self.spool_folder / f"input{i}.txt"
        # Overwrite data dictionary with the input values
        data = self.data.copy()
        for k, v in values.items():
            data[k] = str(v)
        # Dump input file
        with open(input_path, 'w', encoding='utf-16') as f:
            # Write header with EnergyPLAN version
            f.write("EnergyPLAN version\n698\n")
            for k, v in data.items():
                if k == 'EnergyPLAN version':
                    continue
                f.write(f"{k}=\n{v}\n")

    def _dump_inputs(self, x: np.ndarray, input_names: list[str]) -> None:
        self._clean_spool_folder()
        assert len(x.shape) == 2, "Input array must be 2D."
        for i, values in enumerate(x):
            values = {k: v for k, v in zip(input_names, values)}
            self._dump_input(values=values, i=i)

    def _run_energyplan(self, i: int) -> None:
        """
        Execute EnergyPLAN with the `i`-th input file.
        """
        command = [str(self.energyplan_exe),
                   "-i", str(self.spool_folder / f"input{i}.txt"),
                   "-ascii", str(self.results_folder / f"output{i}.txt")]
        subprocess.run(command, check=True)

    @abstractmethod
    def _find_values(self, file_path: Path, *keys: str | tuple[str, str]
                     ) -> np.ndarray:
        """
        Find the values corresponding to `keys` and return them in an array.
        """

    def read_values(self, *keys: str | tuple) -> np.ndarray:
        values = []
        files = list(self.results_folder.glob('*.txt'))
        for file in files:
            values.append(self._find_values(file, *keys))
        return np.vstack(values)

    def _clean_spool_folder(self) -> None:
        """
        Clean the spool folder.
        """
        for file in self.spool_folder.glob("*.txt"):
            file.unlink()

    def _clean_results_folder(self) -> None:
        """
        Clean the results folder.
        """
        for file in self.results_folder.glob("*.txt"):
            file.unlink()


if __name__ == "__main__":
    pass
