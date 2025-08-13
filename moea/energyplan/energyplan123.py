from pathlib import Path

from moea.config import ENERGYPLAN123
from moea.energyplan.energyplan110 import EnergyPLAN110


class EnergyPLAN123(EnergyPLAN110):
    """
    EnergyPLAN model for version 12.3.
    """
    energyplan_path = ENERGYPLAN123

    def __init__(self,
                 energyplan_data_file: str | Path,
                 ) -> None:
        super().__init__(energyplan_data_file)

    def _find_unique_key(self, key: str, lines: list) -> float | None:
        # Stopt after TOTAL ANNUAL COSTS
        for line in lines:
            line = [ln.replace(":", "").strip() for ln in line.split("\0")]
            if key in line:
                for col in line[1:]:
                    if col:
                        return float(col)
            if line[0] == "TOTAL ANNUAL COSTS":
                return

    def _find_tuple_key(self, key: tuple[str, str], lines: list
                        ) -> float | None:
        # Read lines 81 and 82
        ln1 = lines[80].split('\0')
        ln2 = lines[81].split('\0')
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
        for line in lines[83:]:
            line = [ln.replace(":", "").strip() for ln in line.split("\0")]
            if key[0] in line:
                return float(line[j])


if __name__ == "__main__":
    pass
