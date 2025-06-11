from pathlib import Path
from numpy import ndarray
from functools import lru_cache
from moea.energyplan.energyplan_splool import EnergyPLANSpool
from moea.config import ENERGYPLAN163


class EnergyPLAN163(EnergyPLANSpool):

    energyplan_path = ENERGYPLAN163

    def __init__(self,
                 energyplan_data_file: str | Path,
                 input_names: list[str]
                 ) -> None:
        super().__init__(energyplan_data_file, input_names)

    @lru_cache(maxsize=None)
    def _find_position(self, file_path: str | Path, key: str
                      ) -> tuple[int, int] | None:
        """
        Return the line number of a specific key in a file.
        """
        # Open the file and read line by line
        file = open(file_path, 'r', encoding='windows-1252')
        i = 0
        while i < 80:
            line = next(file)
            # If the key is a tuple, then continue
            if type(key) == tuple:
                i += 1
                continue
            # Read the line and split it by tabs
            line = [ln.strip() for ln in line.split('\t')]
            for j, col in enumerate(line):
                if key in col:
                    file.close()
                    return i, j + 1
            i += 1
        # Read lines 81 and 82
        ln1 = next(file).split('\t')
        ln2 = next(file).split('\t')
        i += 2
        # Create keys by joining the two lines
        keys = [f"{ln1[i].strip()} {ln2[i].strip()}" for i in range(len(ln1))]
        # Find the column index
        for j, k in enumerate(keys):
            if key[1] in k:
                break

        if j == len(keys) - 1:
            file.close()
            raise ValueError(
                f"Colunm '{key[1]}' not found in in the list of columns {keys}"
            )

        # Look for the row index, after row 104 there are hourly values
        while i < 104:
            line = next(file)
            if key[0] in line:
                file.close()
                return i, j
            i += 1

        if not file.closed:
            file.close()


if __name__ == "__main__":
    pass
