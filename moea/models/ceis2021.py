import numpy as np
import pandas as pd
from pathlib import Path

from moea.config import PROJ_ROOT, ENERGYPLAN161
from moea.models.base_model import BaseModel
from moea.energyplan.energyplan161 import EnergyPLAN161


ENERGYPLAN_DISTRIBUTIONS_DIR = ENERGYPLAN161 / "EnergyPLAN Data/Distributions"


class CEIS2021(BaseModel):
    """
    The class implements the problem presented in

    > Viesi, D., Mahbub, M. S., Brandi, A., Thellufsen, J. Z., Østergaard,
    > P. A., Lund, H., ... & Crema, L. (2023). Multi-objective optimization of
    > an energy community: an integrated and dynamic approach for full
    > decarbonisation in the European Alps. **International Journal of
    > Sustainable Energy Planning and Management**, 38, 8-29.

    """

    energyplan_version = EnergyPLAN161

    averageKMPerYearPerCar = 12900

    def __init__(self,
                 year: int | None = 2030,
                 data_file: str | Path | None = None,
                 **kwargs):
        """
        Variables need to be provided as an input because their bounds change
        with the scenario year.

        Parameters
        ----------
        - ``year`` : int
            The year of the scenario.

        The initialization method reads the data file, and stores the variables
        and the scenario in the object. It also reads the thermal demand
        distribution and the solar thermal production distribution.

        - ``data_file`` : str
            The path to the data file.
        - ``vars`` : dict
            A dictionary where each key is a variable name and each value is a
            dictionary with the following keys:
                - ``lb`` : float
                    The lower bound of the variable.
                - ``ub`` : float
                    The upper bound of the variable.
        - ``scenario`` : dict
            A dictionary with the following keys:
                - ``totalHeatDemand`` : float
                    The total heat demand.
                - ``coalBoilerEfficiency`` : float
                    The coal boiler efficiency.
                - ``oilBoilerEfficiency`` : float
                    The oil boiler efficiency.
                - ``nGasBoilerEfficiency`` : float
                    The natural gas boiler efficiency.
                - ``biomassBoilerEfficiency`` : float
                    The biomass boiler efficiency.
                - ``efficiencyDieselCar`` : float
                    The efficiency of diesel cars.
                - ``efficiencyEVCar`` : float
                    The efficiency of electric cars.
                - ``efficiencyH2Car`` : float
                    The efficiency of hydrogen cars.
                - ``totalKMRunByCars`` : float
                    The total kilometers run by cars.
                - ``efficiencyElectrolyzer`` : float
                    The efficiency of the electrolyzer.
        """
        self.year = year
        if self.year is None:
            self.year = 2030

        if data_file is None:
            data_file = f"CEIS_{self.year}_BAU.txt"

        # Set the scenario
        self.scenario = pd.read_csv(
            PROJ_ROOT / 'docs/use-cases/ceis2021-scenarios.csv',
            index_col=0
        )
        self.scenario = self.scenario[f'{self.year}'].to_dict()
        # Set the variables
        self.vars = pd.read_csv(
            PROJ_ROOT / f'docs/use-cases/ceis{self.year}.csv',
            index_col=0
        )

        self.thermal_demand = self._read_thermal_demand()

        self.solar_production = self._read_solar_production()

        super().__init__(
            n_var=len(self.vars),
            n_obj=2,
            n_ieq_constr=3,
            xl=self.vars['lb'].values,
            xu=self.vars['ub'].values,
            data_file=data_file,
            **kwargs
        )

    def _read_thermal_demand(self):
        # Retrieve thermal demand distribution and store it as a numpy array
        return pd.read_csv(
            ENERGYPLAN_DISTRIBUTIONS_DIR / \
                f"CEIS_Thermal_Demand_LC_{self.year}.txt",
            names=["heat_demand"]
        )["heat_demand"].values

    def _read_solar_production(self):
        # Retrieve solar thermal production distribution and store it as a
        # numpy array
        return pd.read_csv(
            ENERGYPLAN_DISTRIBUTIONS_DIR / \
                f"CEIS_SolarThermal_Hourly_Production_{self.year}.txt",
            names=["solar_production"]
        )["solar_production"].values

    def _repair_heat(self, v):
        # Get heat demand variables ranges
        mask = self.vars['category'] == 'Heat demand'
        heatDemansRanges = self.vars[mask].ub - self.vars[mask].lb
        for i, ind in enumerate(v[:, mask]):
            diff = ind.sum() - self.scenario['totalHeatDemand']
            while np.abs(diff) > 0.05:
                if ind.sum() > self.scenario['totalHeatDemand']:
                    for j, val in enumerate(ind):
                        red = (ind.sum() - self.scenario['totalHeatDemand']) * \
                            heatDemansRanges.iloc[j] / heatDemansRanges.sum()
                        ind[j] = np.max([self.vars[mask].lb.iloc[j],
                                         val - red])
                else:
                    for j, val in enumerate(ind):
                        inc = \
                            (self.scenario['totalHeatDemand'] - ind.sum()) * \
                            heatDemansRanges.iloc[j] / heatDemansRanges.sum()
                        ind[j] = np.min([self.vars[mask].ub.iloc[j],
                                         val + inc])
                diff = ind.sum() - self.scenario['totalHeatDemand']
            v[i, mask] = ind
        return v

    def _repair_transport(self, v):
        mask = self.vars['category'] == 'Transport'
        transportRanges = self.vars[mask].ub - self.vars[mask].lb
        for i, ind in enumerate(v[:, mask]):
            diff = ind.sum() - self.scenario['totalKMRunByCars']
            while np.abs(diff) > 10:
                if ind.sum() > self.scenario['totalKMRunByCars']:
                    for j, val in enumerate(ind):
                        red = (ind.sum() - self.scenario['totalKMRunByCars']) * \
                            transportRanges.iloc[j] / transportRanges.sum()
                        ind[j] = np.max([self.vars[mask].lb.iloc[j],
                                         val - red])
                else:
                    for j, val in enumerate(ind):
                        inc = \
                            (self.scenario['totalKMRunByCars'] - ind.sum()) * \
                            transportRanges.iloc[j] / transportRanges.sum()
                        ind[j] = np.min([self.vars[mask].ub.iloc[j],
                                         val + inc])
                diff = ind.sum() - self.scenario['totalKMRunByCars']
            v[i, mask] = ind
        return v

    def _evaluate(self, x, out, *args, **kwargs):

        # We operate on a copy of the variables
        v = x.copy()

        # Repair the variables
        v = self._repair_heat(v)
        v = self._repair_transport(v)

        #######################################################################
        # Write input files:
        # Some of the variables are subject to changes before being written
        #######################################################################
        # Battery 1 sets the value of three EnergyPLAN inputs
        battery1 = v[:, self.vars.index.get_loc('input_cap_pump_el')].copy()
        # Electric storage capacity for turbine
        v[:, self.vars.index.get_loc('input_cap_pump_el')] = battery1 * 1e3 / 2
        # Electric storage capacity for pump
        v[:, self.vars.index.get_loc('input_cap_turbine_el')] = battery1 * 1e3 / 2
        # Electric storage capacity for Storage
        v[:, self.vars.index.get_loc('input_storage_pump_cap')] = battery1

        # Coal boiler heat demand
        v[:, self.vars.index.get_loc('input_fuel_Households[1]')] /= \
            self.scenario['coalBoilerEfficiency']
        # Oil boiler heat demand
        v[:, self.vars.index.get_loc('input_fuel_Households[2]')] /= \
            self.scenario['oilBoilerEfficiency']
        # NGas boiler heat demand
        v[:, self.vars.index.get_loc('input_fuel_Households[3]')] /= \
            self.scenario['nGasBoilerEfficiency']
        # Biomass boiler heat demand
        v[:, self.vars.index.get_loc('input_fuel_Households[4]')] /= \
            self.scenario['biomassBoilerEfficiency']

        #################
        # Solar thermal #
        #################
        solarThermalMask = self.vars['category'] == 'Solar Thermal'
        heatDemandMask = self.vars['category'] == 'Heat demand'
        # Update variables
        v[:, solarThermalMask] = v[:, solarThermalMask] * v[:, heatDemandMask]
        # Store total solar thermal for later use in PV constraint calculation
        totalSolarThermalInput = np.sum(
            v[:, solarThermalMask] * v[:, heatDemandMask],
            axis=1
        )
        assert len(totalSolarThermalInput) == len(v)

        #############
        # Transport #
        #############
        # Diesel car demand in km is used to set 2 EnergyPLAN inputs
        dieselDemand = v[:, self.vars.index.get_loc('input_fuel_Transport[2]')].copy()
        # Diesel car fuel demand
        v[:, self.vars.index.get_loc('input_fuel_Transport[2]')] = \
            dieselDemand * self.scenario['efficiencyDieselCar'] / 1e6
        # Number of diesel cars
        key = 'Input_Size_transport_conventional_cars'
        v[:, self.vars.index.get_loc(key)] = \
            dieselDemand / self.averageKMPerYearPerCar
        # Electric car demand in km is used to set 2 EnergyPLAN inputs
        electriCarDemand = v[:, self.vars.index.get_loc('input_transport_TWh')].copy()
        # Electric car demand
        v[:, self.vars.index.get_loc('input_transport_TWh')] = \
            electriCarDemand * self.scenario['efficiencyEVCar'] / 1e6
        # Number of electric cars
        key = 'Input_Size_transport_electric_cars'
        v[:, self.vars.index.get_loc(key)] = \
            electriCarDemand / self.averageKMPerYearPerCar
        # Hydrogen car demand
        v[:, self.vars.index.get_loc('input_fuel_Transport[6]')] *= \
            (self.scenario['efficiencyH2Car'] / 1e6)

        # Call EnergyPLAN using spool mode; only the input files are needed
        self.energyplan.run(
            [{self.vars.index[j]: ind[j] for j in range(len(ind))}
             for ind in v]
        )

        z = self.energyplan.read_values(
            "CO2-emission (total)",
            ("Annual", "Import Electr."),
            "Variable costs",
            "Fixed operation costs",
            "Annual Investment costs",
            "Bottleneck",
            ("Annual", "Electr. Demand"),
            ("Annual", "HH-HP Electr."),
            ("Annual", "FWPump Electr."),
            ("Annual", "Pump Electr."),
            ("Annual Maximum", "H2 Electr."),
            ("Annual Maximum", "Import Electr."),
            ("Annual Maximum", "Export Electr."),
        ).T

        CO2 = 0
        IMPORT = 1
        VAR_COST = 2
        FIX_COST = 3
        INV_COST = 4
        BOTTLENECK = 5
        ELEC_DEMAND = 6
        HH_HP_ELEC = 7
        FWPUMP = 8
        PUMP_ELEC = 9
        H2_ELEC = 10
        MAX_IMPORT = 11
        MAX_EXPORT = 12

        if self.year == 2030:
            co2InImportedEleOil = z[IMPORT] / 0.53 * 0.66 / 100 * 0.267
            co2InImportedEleNGas = z[IMPORT] / 0.53 * 43.94 / 100 * 0.202
        elif self.year == 2050:
            co2InImportedEleOil = z[IMPORT] / 0.56 * 0.00 / 100 * 0.267
            co2InImportedEleNGas = z[IMPORT] / 0.56 * 12.00 / 100 * 0.202

        localCO2emission = z[CO2] + co2InImportedEleOil + \
            co2InImportedEleNGas

        z[VAR_COST] -= z[BOTTLENECK]

        # Retrieve the annual H2mCHP heat demand from the variables
        # In the first implementation we retrieved input_HH_H2CHP_heat
        annualH2mCHPHeat = v[:, self.vars.index.get_loc('input_HH_H2CHP_heat')]

        investmentCostAnnualH2mCHPheat = \
            ((annualH2mCHPHeat * 1e6 / 15000) *  3.725 * 0.03) / \
                (1 - np.pow(1 + 0.03, -20))

        z[INV_COST] +=  investmentCostAnnualH2mCHPheat

        operationalCostAnnualH2mCHPheat = \
            (annualH2mCHPHeat * 1e6 / 15000) * 0.0417 * 3.725

        z[FIX_COST] += operationalCostAnnualH2mCHPheat

        annualnGasmCHPHeat = v[:, self.vars.index.\
                               get_loc('input_HH_NgasCHP_heat')]
        FU_N_Gas_CHP = 0.284618279
        investmentCostAnnualnGasmCHPheat = (
            (annualnGasmCHPHeat * 1e6 / 15000) * \
                ((0.9 * 1000 * self.scenario['nGasCoeff1'] * 15) / \
                 (self.scenario['nGasCoeff2'] * FU_N_Gas_CHP * 366 * 24)) * 0.03) / \
                    (1 - np.pow(1 + 0.03, -20)) + \
                        annualnGasmCHPHeat * 0.174 * 3600 * 0.03 / \
                            (1 - np.pow(1 + 0.03, -40))

        z[INV_COST] += investmentCostAnnualnGasmCHPheat

        operationalCostAnnualnGasmCHPheat = \
            (annualnGasmCHPHeat * 1e6 / 15000) * \
                self.scenario['nGasHeatCoeff'] * \
                ((0.9 * 1000 * self.scenario['nGasCoeff1'] * 15) / \
                (0.48 * FU_N_Gas_CHP * 366 * 24)) + \
                    annualnGasmCHPHeat * 0.0076 * 0.174 * 3600

        z[FIX_COST] += operationalCostAnnualnGasmCHPheat

        annualBiomassmCHPHeat = v[:, self.vars.index.\
                                  get_loc('input_HH_BioCHP_heat')]
        FU_Biogas_CHP = 0.284618279
        investmentCostBiomassmCHP = (
            (annualBiomassmCHPHeat * 1e6 / 15000) * \
                ((self.scenario['biomassCoeff1'] * 1000 *
                  self.scenario['biomassCoeff2'] * 15) /
                  (self.scenario['biomassCoeff3'] * FU_Biogas_CHP * 366 * 24))
                  * 0.03) / (1 - np.pow(1 + 0.03,-20)) + \
                    annualBiomassmCHPHeat * 0.174 * 3600 * 0.03 / \
                        (1 - np.pow(1 + 0.03, -40))

        z[INV_COST] += investmentCostBiomassmCHP

        operationalCostBiomassmCHP = \
            (annualBiomassmCHPHeat * 1e6 / 15000) * self.scenario['biomassCoeff4'] * \
                ((self.scenario['biomassCoeff1'] * 1000 *
                  self.scenario['biomassCoeff2'] * 15) /
                (self.scenario['biomassCoeff3'] * FU_Biogas_CHP * 366 * 24)) \
                    + annualBiomassmCHPHeat * 0.0076 * 0.174 * 3600

        z[FIX_COST] += operationalCostBiomassmCHP

        elCarDemandInGWh = \
            electriCarDemand * self.scenario['efficiencyEVCar'] / 1e6
        h2CarDemandInKM = v[:, self.vars.index.\
                            get_loc('input_fuel_Transport[6]')] / (self.scenario['efficiencyH2Car'] / 1e6)
                            #get_loc('input_fuel_Transport[6]')]
        # Cost for H2 cars
        elForH2ForTransport = h2CarDemandInKM * self.scenario['efficiencyH2Car'] / self.scenario['efficiencyElectrolyzer'] / 1e6
        elForH2Heat = annualH2mCHPHeat / 0.97 / 0.7217 / 1e6

        elecGridDistributionCost = self.scenario['gridCost'] * \
            (1 - self.scenario['gridCostCoeff']) * \
                (z[ELEC_DEMAND] + elCarDemandInGWh + z[HH_HP_ELEC] +
                 z[FWPUMP] + z[PUMP_ELEC] + elForH2ForTransport + elForH2Heat -
                 z[IMPORT]) + self.scenario['gridCost'] * z[IMPORT]

        z[VAR_COST] += elecGridDistributionCost

        varibleCostForH2 = (annualH2mCHPHeat / self.scenario['H2CostCoeff']) \
            * self.scenario['H2Cost']

        z[VAR_COST] += varibleCostForH2

        # Cost for H2 cars
        investmentCostForH2Cars = \
            h2CarDemandInKM / self.averageKMPerYearPerCar * self.scenario['H2CarsCost'] * 0.03 / \
                (1 - np.pow(1 + 0.03, -12)) + h2CarDemandInKM / \
                    self.averageKMPerYearPerCar * self.scenario['H2CarsCoeff1'] * 0.03 / \
                        (1 - np.pow(1 + 0.03, -12))

        z[INV_COST] += investmentCostForH2Cars

        operationalCostForH2Cars = h2CarDemandInKM / 12900 * \
            self.scenario['H2CarsCoeff2'] * self.scenario['H2CarsCost'] + \
                (h2CarDemandInKM / 12900) * self.scenario['H2CarsCoeff2'] * \
                    self.scenario['H2CarsCoeff3']

        z[FIX_COST] += operationalCostForH2Cars

        investmentCostForSolarHeatStorage = 0
        operationalCostForSolarHeatStorage = 0
        # Cost for solar heat storage
        for _, row in self.vars.iterrows():
            if row['category'] == "Solar storage":
                solarStorageInDays = v[:, self.vars.index.get_loc(row.name)]
                heatDemand = v[:, self.vars.index.get_loc(row.name) - 8]
                investmentCostForSolarHeatStorage += \
                    solarStorageInDays * heatDemand / 366 * 3000 * 0.03 / \
                        (1 - np.pow(1 + 0.03, -30))
                operationalCostForSolarHeatStorage += \
                    solarStorageInDays * 0.007 * heatDemand / 366 * 3000

        z[INV_COST] += investmentCostForSolarHeatStorage
        z[FIX_COST] += operationalCostForSolarHeatStorage

        # Building cost
        investmentCostForEnergyEfficiencyBuilding = \
            self.scenario['buildingCost'] * 3300 * 0.03 / \
                (1 - np.pow(1 + 0.03, -30))

        z[INV_COST] += investmentCostForEnergyEfficiencyBuilding

        # Calculate the cost for the H2 electrolyzer
        electrolyzerInvestmentCost = (
                (z[H2_ELEC] * self.scenario['electrolyzerInvestmentUnitCost'])
                * 0.03) / (1 - np.pow(1 + 0.03, - self.scenario['lifeTime']))

        z[INV_COST] += electrolyzerInvestmentCost

        # addtional OM cost
        electrolyzerOMCost = \
            (z[H2_ELEC] * self.scenario['electrolyzerInvestmentUnitCost']) * \
                self.scenario['electrolyzerOMUnitCost'] / 100

        z[INV_COST] += electrolyzerOMCost

        actualAnnualCost = z[VAR_COST] + z[FIX_COST] + z[INV_COST]

        out["F"] = np.array([localCO2emission, actualAnnualCost]).T

        # Calculation of constraints
        # TODO: id totalSolaerThermalInput updated before using it here? Last update was when writing variables.
        # PV constraint
        PV_land = (v[:, self.vars.index.get_loc('input_RES2_capacity')] - 636.72) / \
            self.scenario['PVCapCoeff1']
        solar_thermal_land = (totalSolarThermalInput * 1e6 /
            self.scenario['PVCapCoeff2'])
        PVConstraint = - self.scenario['totalLand'] + PV_land + solar_thermal_land
        # Import constraint
        importConstraint = - z[MAX_IMPORT]
        # Export constraint
        exportConstraint = - z[MAX_EXPORT]

        out["G"] = np.column_stack([
            PVConstraint,
            importConstraint,
            exportConstraint
        ])


if __name__ == "__main__":
    pass
