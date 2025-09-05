import numpy as np
from pathlib import Path

from moea.config import ENERGYPLAN110
from moea.energyplan.energyplan_base import EnergyPLANBase


class EnergyPLAN110(EnergyPLANBase):
    """
    EnergyPLAN model for version 11.0.
    """
    energyplan_path = ENERGYPLAN110

    def __init__(self,
                 energyplan_data_file: str | Path,
                 ) -> None:
        super().__init__(energyplan_data_file)

    def _find_unique_key(self, key: str, lines: list) -> float | None:
        # Stopt after TOTAL ANNUAL COSTS
        for line in lines:
            line = [ln.replace("=", "").strip() for ln in line.split("\0")]
            if key in line:
                for col in line[1:]:
                    if col:
                        return float(col.replace(",", "."))
            if line[0] == "TOTAL ANNUAL COSTS":
                return

    def _find_tuple_key(self, key: tuple[str, str], lines: list
                        ) -> float | None:
        # Find TOTAL ANNUAL COST line
        for i, line in enumerate(lines):
            line = [ln.replace("=", "").strip() for ln in line.split("\0")]
            if line[0] == "TOTAL ANNUAL COSTS":
                break
        # Read lines 81 and 82
        ln1 = lines[i + 3].split('\0')
        ln2 = lines[i + 4].split('\0')
        # Create keys by joining the two lines
        keys = [f"{ln1[i].strip()} {ln2[i].strip()}".strip()
                for i in range(len(ln1))]
        # Find the column index
        for j, k in enumerate(keys):
            if key[1] == k:
                break
        if j == len(keys) - 1:
            raise ValueError(
                f"Colunm '{key[1]}' not found in in the list of columns {keys}"
            )

        # Look for the row index, after row 104 there are hourly values
        for line in lines[i + 5:]:
            line = [ln.replace(":", "").strip() for ln in line.split("\0")]
            if key[0] in line:
                return float(line[j])

    def _find_values(self, file_path: Path, *keys: str | tuple[str, str]):
        """
        Find the value of a key in a file. The value is assumed to be in the
        line immediately after the key.
        """
        values = []
        with open(file_path, 'r', encoding='windows-1252') as f:
            lines = f.readlines()
            for key in keys:
                if isinstance(key, str):
                    value = self._find_unique_key(key, lines)
                elif isinstance(key, tuple):
                    value = self._find_tuple_key(key, lines)
                else:
                    raise ValueError("The key must be a string or a tuple.")
                if value is not None:
                    values.append(value)
                else:
                    raise ValueError(f"Key {key} not found.")
        return np.array(values)


if __name__ == "__main__":
    pass
