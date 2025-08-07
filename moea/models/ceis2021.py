import numpy as np
import pandas as pd
from pathlib import Path

from moea.config import PROJ_ROOT, ENERGYPLAN161
from moea.models.base_model import BaseModel
from moea.energyplan.energyplan161 import EnergyPLAN161


ENERGYPLAN_DISTRIBUTIONS_DIR = ENERGYPLAN161 / "EnergyPLAN Data/Distributions"


class CEIS2021(BaseModel):

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
        # Battery 1
        # Electric storage capacity for turbine
        v[:, self.vars.index.get_loc('input_cap_pump_el')] *= 1e3 / 2
        # Electric storage capacity for pump
        v[:, self.vars.index.get_loc('input_cap_turbine_el')] *= 1e3 / 2
        # Electric storage capacity for Storage
        v[:, self.vars.index.get_loc('input_storage_pump_cap')] *= 1e3
        ########
        # Heat #
        ########
        # Fuel demands for heating
        # In the original code by Mahbub, there's also a key named
        # coilBoilerFuelDemand that is set to coalBoilerHeatDemand /
        # coalBoilerEfficiency. However, this key is never used anywhere in
        # the code. I'm not sure if it's a mistake or if it's used somewhere
        v[:, self.vars.index.get_loc('input_fuel_Households[1]')] /= \
            self.scenario['coalBoilerEfficiency']
        v[:, self.vars.index.get_loc('input_fuel_Households[2]')] /= \
            self.scenario['oilBoilerEfficiency']
        v[:, self.vars.index.get_loc('input_fuel_Households[3]')] /= \
            self.scenario['nGasBoilerEfficiency']
        v[:, self.vars.index.get_loc('input_fuel_Households[4]')] /= \
            self.scenario['biomassBoilerEfficiency']
        #################
        # Solar thermal #
        #################
        solarThermalMask = self.vars['category'] == 'Solar Thermal'
        heatDemandMask = self.vars['category'] == 'Heat demand'
        totalSolarThermalInput = np.sum(
            v[:, solarThermalMask] * v[:, heatDemandMask],
            axis=1
        )
        assert len(totalSolarThermalInput) == len(v)

        #############
        # Transport #
        #############
        # Diesel car fuel demand
        v[:, self.vars.index.get_loc('input_fuel_Transport[2]')] *= \
            self.scenario['efficiencyDieselCar'] / 1e6
        # Number of diesel cars
        key = 'Input_Size_transport_conventional_cars'
        v[:, self.vars.index.get_loc(key)] /= self.averageKMPerYearPerCar
        # Electric car demand
        v[:, self.vars.index.get_loc('input_transport_TWh')] *= \
            self.scenario['efficiencyEVCar'] / 1e6
        # Number of electric cars
        key = 'Input_Size_transport_electric_cars'
        v[:, self.vars.index.get_loc(key)] /= self.averageKMPerYearPerCar
        # Hydrogen car demand
        v[:, self.vars.index.get_loc('input_fuel_Transport[6]')] *= \
            self.scenario['efficiencyH2Car'] / 1e6

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
            co2InImportedEleOil = z[IMPORT] / 0.56 * 0.00 / 100 * 0.267  #TODO: c'e una moltiplicazione per zero qui!!!
            co2InImportedEleNGas = z[IMPORT] / 0.56 * 12.00 / 100 * 0.202

        localCO2emission = z[CO2] + co2InImportedEleOil + \
            co2InImportedEleNGas

        z[VAR_COST] -= z[BOTTLENECK]

        # Retrieve the annual H2mCHP heat demand from the variables
        annualH2mCHPHeat = v[:, self.vars.index.\
                             get_loc('input_HH_H2CHP_storage')]
        #TODO: Calculation of the annual investment cost is the same for 2030 and 2050
        investmentCostAnnualH2mCHPheat = \
            ((annualH2mCHPHeat * 1e2 / 1.5) *  3.725 * 0.03) / \
                (1 - np.pow(1 + 0.03, -20))

        z[INV_COST] +=  investmentCostAnnualH2mCHPheat

        #TODO: Calculation of the annual operational cost is the same for 2030 and 2050
        operationalCostAnnualH2mCHPheat = \
            (annualH2mCHPHeat * 1e2 / 1.5) * 0.0417 * 3.725

        z[FIX_COST] += operationalCostAnnualH2mCHPheat

        annualnGasmCHPHeat = x[:, self.vars.index.\
                               get_loc('input_HH_NgasCHP_heat')]
        FU_N_Gas_CHP = 0.284618279
        investmentCostAnnualnGasmCHPheat = (
            (annualnGasmCHPHeat * 1e2 / 1.5) * \
                ((0.9 * 1000 * self.scenario['nGasCoeff1'] * 15) / \
                 (self.scenario['nGasCoeff2'] * FU_N_Gas_CHP * 366 * 24)) * 0.03) / \
                    (1 - np.pow(1 + 0.03, -20)) + \
                        annualnGasmCHPHeat * 0.174 * 3600 * 0.03 / \
                            (1 - np.pow(1 + 0.03, -40))

        z[INV_COST] += investmentCostAnnualnGasmCHPheat

        operationalCostAnnualnGasmCHPheat = \
            (annualnGasmCHPHeat * 1e2 / 1.5) * \
                self.scenario['nGasHeatCoeff'] * \
                ((0.9 * 1000 * self.scenario['nGasCoeff1'] * 15) / \
                (0.48 * FU_N_Gas_CHP * 366 * 24)) + \
                    annualnGasmCHPHeat * 0.0076 * 0.174 * 3600

        z[FIX_COST] += operationalCostAnnualnGasmCHPheat

        annualBiomassmCHPHeat = x[:, self.vars.index.\
                                  get_loc('input_HH_BioCHP_heat')]
        FU_Biogas_CHP = 0.284618279
        investmentCostBiomassmCHP = (
            (annualBiomassmCHPHeat * 1e2 / 1.5) * \
                ((self.scenario['biomassCoeff1'] * 1000 *
                  self.scenario['biomassCoeff2'] * 15) /
                  (self.scenario['biomassCoeff3'] * FU_Biogas_CHP * 366 * 24))
                  * 0.03) / (1 - np.pow(1 + 0.03,-20)) + \
                    annualBiomassmCHPHeat * 0.174 * 3600 * 0.03 / \
                        (1 - np.pow(1 + 0.03, -40))

        z[INV_COST] += investmentCostBiomassmCHP

        operationalCostBiomassmCHP = \
            (annualBiomassmCHPHeat * 1e2 / 1.5) * self.scenario['biomassCoeff4'] * \
                ((self.scenario['biomassCoeff1'] * 1000 *
                  self.scenario['biomassCoeff2'] * 15) /
                (self.scenario['biomassCoeff3'] * FU_Biogas_CHP * 366 * 24)) \
                    + annualBiomassmCHPHeat * 0.0076 * 0.174 * 3600

        z[FIX_COST] += operationalCostBiomassmCHP

        elCarDemandInKM = x[:, self.vars.index.\
                            get_loc('input_transport_TWh')]
        elCarDemandInGWh = \
            elCarDemandInKM * self.scenario['efficiencyEVCar'] / 1e6
        h2CarDemandInKM = x[:, self.vars.index.\
                            get_loc('input_fuel_Transport[6]')]
        # Cost for H2 cars
        elForH2ForTransport = h2CarDemandInKM * 0.239 / 0.7217 / 1e6
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
            h2CarDemandInKM / 12900 * self.scenario['H2CarsCost'] * 0.03 / \
                (1 - np.pow(1 + 0.03, -12)) + h2CarDemandInKM / \
                    12900 * self.scenario['H2CarsCoeff1'] * 0.03 / \
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
                solarStorageInDays = x[:, self.vars.index.get_loc(row.name)]
                heatDemand = x[:, self.vars.index.get_loc(row.name) - 8]
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

        out["F"] = np.array([localCO2emission, actualAnnualCost])

        # Calculation of constraints
        for _, row in self.vars.iterrows():
            if row['category'] == "Heat demand":
                heatDemand = x[:, self.vars.index.get_loc(row.name)]
                solarInput = x[:, self.vars.index.get_loc(row.name) + 8]
                solarStorage = x[:, self.vars.index.get_loc(row.name) + 16]
                xSolarInput = True if row.name == 'input_HH_HP_solar' \
                    else False
                # Solar utilization caluculation changes when considering HP
                solarUtilization = self.solarUtilization(
                    heatDemand, solarInput, solarStorage, xSolarInput
                )

        # PV constraint
        PVConstraint = self.scenario['totalLand'] - \
            (x[:, self.vars.index.get_loc('input_RES2_capacity')] - 636.72) / \
                self.scenario['PVCapCoeff1'] + \
                    (totalSolarThermalInput * 1e6 /
                     self.scenario['PVCapCoeff2'])
        # Import constraint
        importConstraint = - z[MAX_IMPORT]
        # Export constraint
        exportConstraint = - z[MAX_EXPORT]

        out["G"] = np.column_stack([
            PVConstraint,
            importConstraint,
            exportConstraint
        ])


    def solarUtilization(self, heatDemand, solarInput, storageDays,
                         xSolarInput=False):
        # Compute scalar values
        totalSolarProduction = self.solar_production.sum()
        totalThermalDemand = self.thermal_demand.sum()

        storage = (heatDemand / 8784) * storageDays * 24

        hourProduction = \
            np.expand_dims(self.solar_production, 0).T * \
            np.expand_dims(solarInput, 0) / \
            totalSolarProduction
        hourDemand = \
            np.expand_dims(self.thermal_demand, 0).T * \
            np.expand_dims(heatDemand, 0) / \
            totalThermalDemand

        mask = hourProduction <= hourDemand

        delta = hourDemand - hourProduction

        # Initialize space for solar utilization
        solarUtilization = np.zeros(len(heatDemand))
        storageContent = np.zeros_like(heatDemand)

        stop = 10 if xSolarInput else 1
        iter = 0

        percentage = np.zeros_like(heatDemand)
        start, end = np.zeros_like(heatDemand), np.zeros_like(heatDemand)

        while iter < stop or np.any(percentage >= 10):
            # Select only individuals with a percentage greater than 10
            fx = percentage >= 10

            start[fx] = end[fx]
            storageContent[fx] = start[fx]
            utilization = np.zeros_like(heatDemand)
            for i in range(len(self.solar_production)):

                utilization[fx] = np.where(
                    mask[i, fx],
                    utilization[fx] + hourProduction[i, fx] + \
                        np.minimum(storageContent[fx], delta[i, fx]),
                    utilization[fx] + hourDemand[i, fx]
                )

                storageContent[fx] = np.where(
                    mask[i, fx],
                    storageContent[fx] - np.minimum(storageContent[fx],
                                                    delta[i, fx]),
                    storageContent[fx] - delta[i, fx]
                )

                storageContent[fx] = np.where(
                    mask[i, fx],
                    np.maximum(storageContent[fx], 0),
                    np.minimum(storageContent[fx], storage[fx])
                )

            end[fx] = storageContent[fx]

            eps = 1e-6

            percentage[fx] = np.where(
                np.abs(start[fx] - end[fx]) != 0,
                np.abs(start[fx] - end[fx]) / \
                    np.maximum(start[fx] + eps, end[fx] + eps) * 100,
                0
            )
            iter += 1
        return solarUtilization
