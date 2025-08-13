from pathlib import Path
from moea.config import ENERGYPLAN161
from moea.energyplan.energyplan163 import EnergyPLAN163


class EnergyPLAN161(EnergyPLAN163):

    energyplan_path = ENERGYPLAN161

    def __init__(self,
                 energyplan_data_file: str | Path,
                 ) -> None:
        super().__init__(energyplan_data_file)


if __name__ == "__main__":
    pass
