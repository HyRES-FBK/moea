import subprocess
import numpy as np
from pathlib import Path
from abc import abstractmethod
from functools import lru_cache
from moea.energyplan.energyplan_base import EnergyPLANBase


class EnergyPLANSpool(EnergyPLANBase):

    def __init__(self,
                 energyplan_data_file: str | Path,
                 ) -> None:
        super().__init__(energyplan_data_file)

    def run(self, inputs: list[dict[str, float | str]]) -> None:
        """
        Run EnergyPLAN with values in `x` and write results in the results
        folder.
        """
        self._clean_results_folder()
        self._clean_spool_folder()
        # Dump inputs to files
        for i, values in enumerate(inputs):
            self._dump_input(values, i)
        self._run_energyplan_spool(n_files=len(inputs))

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

    @lru_cache(maxsize=None)
    def _find_positions(self, file_path: str | Path, *keys: str) -> np.ndarray:
        """
        Return an array with row and column positions for a list of keys.
        """
        positions = []
        for key in keys:
            positions.append(self._find_position(file_path, key))
        return np.stack(positions)

    def _find_values(self, file_path: Path, *keys: str | tuple[str, str]
                     ) -> np.ndarray:
        """
        Find the value of a key in a file. The value is assumed to be in the
        line immediately after the key.
        """
        idxs = self._find_positions(file_path, *keys)
        values = []
        with open(file_path, 'r', encoding='windows-1252') as f:
            lines = f.readlines()
            for i, j in idxs:
                values.append(
                    float(lines[i].split('\t')[j].strip().replace(',', '.'))
                )
        return np.array(values)


if __name__ == "__main__":
    pass
