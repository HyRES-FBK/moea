from pathlib import Path
from abc import abstractmethod
import subprocess
import numpy as np
from moea.energyplan.energyplan_base import EnergyPLANBase


class EnergyPLANSpool(EnergyPLANBase):

    def __init__(self,
                 energyplan_data_file: str | Path,
                 input_names: list[str]
                 ) -> None:
        super().__init__(energyplan_data_file, input_names)

    def spool(self, x: np.ndarray) -> None:
        """
        Run EnergyPLAN with values in `x` and write results in the results
        folder.
        """
        self._clean_results_folder()
        self._clean_spool_folder()
        assert x.shape[1] == len(self.input_names)
        # Dump inputs to files
        for i, values in enumerate(x):
            self._dump_input(values, i)
        self._run_energyplan_spool(n_files=x.shape[0])

    def _run_energyplan_spool(self, n_files: int) -> None:
        """
        Execute EnergyPLAN with the `i`-th input file.
        """
        input_files = [f"input{i}.txt" for i in range(n_files)]
        subprocess.run([str(self.energyplan_exe),
                        "-spool", str(n_files),
                        *input_files,
                        "-ascii", "run"])

    @abstractmethod
    def _find_position(self, file_path: str | Path, key: str
                      ) -> tuple[int, int]:
        """
        Return the line number of a specific key in a file.
        """
        raise NotImplementedError

    def _find_positions(self, file_path: str | Path, *keys: str) -> np.ndarray:
        """
        Return an array with row and column positions for a list of keys.
        """
        positions = []
        for key in keys:
            positions.append(self._find_position(file_path, key))
        return np.stack(positions)


if __name__ == "__main__":
    pass
