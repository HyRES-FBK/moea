import numpy as np
import pandas as pd
from pathlib import Path


ENERGYPLAN_RESULTS = "results"
from moea.config import logger
from moea.models.base_model import BaseModel
from moea.energyplan.energyplan123 import EnergyPLAN123


class ValDiNon(BaseModel):
    """
    This problem class replicates the model in {cite:ps}`MAHBUB20171487`.

    The problem implementation refers [this implementation]
    (https://github.com/shaikatcse/EnergyPLANDomainKnowledgeEAStep1/blob/master/src/reet/fbk/eu/OptimizeEnergyPLANVdN/problem/EnergyPLANProblemVdN2DWithElecVehicleModifiedCO2.java)
    by Mahbub.

    There is a domain knowledge for each of the objectives. For each domain,
    knowledge is provided in the form of a boolean value. The domains are:
        - ``dk0``: Describes if a variable contributes to minimizing the
        emission of CO2. If ``True``, the variable increases the CO2 emission.
        If ``False``, the variable decreases the CO2 emission. If ``None``,
        the variable does not affect the CO2 emission.
        - ``dk1``: Describes if a variable contributes to minimizing the total
        annual cost. If ``True``, the variable increases the total annual cost.
        If ``False``, the variable decreases the total annual cost. If
        ``None``, the variable does not affect the total annual cost.

    """

    energyplan_version = EnergyPLAN123

    def __init__(self,
                 year: int | None = None,
                 scenario: dict | None = None,
                 data_file: str | Path | None = None,
                 **kwargs):
        """
        If function parameters are not specified, the model is set to the 2020
        scenario.

        Parameters:
        -----------
        - ``year``: int
            The year of the scenario.
        - ``scenario``: dict
            A dictionary containing the scenario data used in the `_evaluate`
            method.
            The dictionary should have the following keys:
                - ``totalHeatDemand`` in GWh;
                - ``efficiencyConCar`` in KWh/km;
                - ``efficiencyEVCar`` in KWh/km divided by 0.85, which is
                "round-trip" battery efficiency;
                - ``efficiencyFCEVCar`` in KWh/km;
                - ``efficiencyBiomassCHP``;
                - ``efficiencyElectrolyzerTrans``;
                - ``oilBoilerEfficiency``;
                - ``nGasBoilerEfficiency``;
                - ``biomassBoilerEfficiency``;
                - ``COP``;
                - ``coalShare``;
                - ``oilShare``;
                - ``nGasShare``;
                - ``additionalCostPerGWhinKEuro``.

        - ``data_file``: str or Path
            The path to the input file. This file is used as a template to
            generate the input files for each individual.
            The values will be replaced by the values of the decision variables
            when generating the input files.
        """

        self.vars = pd.DataFrame.from_dict({
            "PVCapacity": \
                {"lb": 936.0, "ub": 40000.0, "dk0": True, "dk1": False},
            "oilBoilerPercentage": \
                {"lb": 0, "ub": 1, "dk0": False, "dk1": None},
            "nGasBoilerPercentage": \
                {"lb": 0, "ub": 1, "dk0": None, "dk1": None},
            "biomassBoilerPercentage": \
                {"lb": 0, "ub": 1, "dk0": True, "dk1": True},
            "biomassMicroCHPPercentage": \
                {"lb": 0, "ub": 1, "dk0": True, "dk1": False},
            "electricCarPercentage": \
                {"lb": 0, "ub": 1, "dk0": True, "dk1": False},
            "oilBoilerSolarThermalPercentage": \
                {"lb": 0, "ub": 1, "dk0": False, "dk1": False},
            "nGasBoilerSolarThermalPercentage": \
                {"lb": 0, "ub": 1, "dk0": False, "dk1": False},
            "biomassBoilerSolarThermalPercentage": \
                {"lb": 0, "ub": 1, "dk0": True, "dk1": True},
            "biomassMicroCHPSolarThermalPercentage": \
                {"lb": 0, "ub": 1, "dk0": True, "dk1": False},
            "heatPumpSolarThermalPercentage": \
                {"lb": 0, "ub": 1, "dk0": True, "dk1": None},
        }, orient="index")

        # Store the year
        self.year = year
        if self.year is None:
            self.year = 2020
        # Set the scenario
        self.scenario = scenario
        # If no scenario is provided, use the default one
        if self.scenario is None:
            scenario_data_file = Path('docs/use-cases/vdn-scenarios.csv')
            logger.warning(f"No scenario provided. Try to use year {self.year}"
                           f" scenario from {scenario_data_file}.")
            if not scenario_data_file.exists():
                logger.error("No scenario provided and file with scenario "
                             "data not found.")
            self.scenario = pd.read_csv(scenario_data_file, index_col=0)
            if self.year not in self.scenario:
                logger.error(f"Yesr {self.year} not found in "
                             f"{scenario_data_file}.")
            self.scenario = self.scenario[str(self.year)].to_dict()
            logger.success(f"Found scenario data for the year {self.year}.")
        if data_file is None:
            data_file = f"VdN SH Eleboration/VdN_SH_{self.year}_Opt_Scenario_2DS_El_mob.txt"

        # Initialize the parent class
        super().__init__(
            n_var=len(self.vars),
            n_obj=2,
            n_ieq_constr=1,
            xl=self.vars['lb'].values,
            xu=self.vars['ub'].values,
            data_file=data_file,
            **kwargs
        )


    def _evaluate(self, x, out, *args, **kwargs):
        """
        The objective function and constraints are evaluated here. The
        objective function evaluation consists of a call to EnergyPLAN.
        """
        # Heat percentages
        heatPercentages = np.copy(x[:, 1:5])

        heatPercentages = np.sort(heatPercentages, axis=1)

        oilBoilerPercentage = heatPercentages[:, 0]
        nGasBoilerPercentage = heatPercentages[:, 1] - heatPercentages[:, 0]
        biomassBoilerPercentage = heatPercentages[:, 2] - heatPercentages[:, 1]
        biomassMicroCHPPercentage = heatPercentages[:, 3] - heatPercentages[:, 2]
        heatPumpPercentage = 1 - heatPercentages[:, 3]

        # Electric car percentage
        EVCarPercentage = x[:, 5]
        conCarpercentage = 1 - EVCarPercentage

        totalKMRunByConCar = (self.scenario["totalKMRunByCars"] *
                              conCarpercentage).astype(int)
        totalKMRunByEVCar = (self.scenario["totalKMRunByCars"] *
                             EVCarPercentage).astype(int)

        totalDieselDemandInGWhForTrns = totalKMRunByConCar * \
            self.scenario["efficiencyConCar"] / 1e6
        totalElecDemandInGWhForTrns = totalKMRunByEVCar * \
            self.scenario["efficiencyEVCar"] / 1e6

        # Solar thermal percentages
        oilSolarPercentage = x[:, 6]
        nGasSolarPercentage = x[:, 7]
        biomassSolarPercentage = x[:, 8]
        microCHPSolarPercentage = x[:, 9]
        hpSolarPercentage = x[:, 10]

        # Fuel demand for oil boiler
        oilBoilerFuelDemand = oilBoilerPercentage * \
            self.scenario["totalHeatDemand"] / \
            self.scenario["oilBoilerEfficiency"]
        oilSolarThermal = oilBoilerFuelDemand * oilSolarPercentage

        # Fuel demand for nGas boiler
        nGasBoilerFuelDemand = nGasBoilerPercentage * \
            self.scenario["totalHeatDemand"] / \
            self.scenario["nGasBoilerEfficiency"]
        nGasSolarThermal = nGasBoilerFuelDemand * nGasSolarPercentage

        # Fuel demand for biomass boiler
        biomassBoilerFuelDemand = biomassBoilerPercentage * \
            self.scenario["totalHeatDemand"] / \
            self.scenario["biomassBoilerEfficiency"]
        biomassBoilerSolarThermal = biomassBoilerFuelDemand * \
            biomassSolarPercentage

        # Fuel demand for biomass microCHP
        biomassMicroCHPHeatDemand = biomassMicroCHPPercentage * \
            self.scenario["totalHeatDemand"]
        biomassMicroCHPSolarThermal = biomassMicroCHPHeatDemand * \
            microCHPSolarPercentage * self.scenario["efficiencyBiomassCHP"]

        # Fuel demand for heat pump
        heatPumpHeatDemand = heatPumpPercentage * \
            self.scenario["totalHeatDemand"]
        heatPumpSolarThermal = heatPumpPercentage * hpSolarPercentage * \
            self.scenario["totalHeatDemand"]

        # Calculate the number of conventional cars and electric cars
        numberOfConCars = totalDieselDemandInGWhForTrns * 1e6 / \
            (self.scenario["efficiencyConCar"] *
             self.scenario["averageKMPerYearPerCar"] * 1e3)
        numberOfEVCars = totalElecDemandInGWhForTrns * 1e6 / \
            (self.scenario["efficiencyEVCar"] *
             self.scenario["averageKMPerYearPerCar"] * 1e3)

        # Run EnergyPLAN
        self.energyplan.run(
            inputs=[
                {
                    "input_RES1_capacity": x[i, 0].astype(int),
                    "input_fuel_Households[2]": oilBoilerFuelDemand[i],
                    "input_HH_oilboiler_Solar": oilSolarThermal[i],
                    "input_fuel_Households[3]": nGasBoilerFuelDemand[i],
                    "input_HH_ngasboiler_Solar": nGasSolarThermal[i],
                    "input_fuel_Households[4]": biomassBoilerFuelDemand[i],
                    "input_HH_bioboiler_Solar": biomassBoilerSolarThermal[i],
                    "input_HH_BioCHP_heat": biomassMicroCHPHeatDemand[i],
                    "input_HH_BioCHP_solar": biomassMicroCHPSolarThermal[i],
                    "input_HH_HP_heat": heatPumpHeatDemand[i],
                    "input_HH_HP_solar": heatPumpSolarThermal[i],
                    "input_fuel_Transport[5]": totalDieselDemandInGWhForTrns[i],
                    "Input_Size_transport_conventional_cars": numberOfConCars[i],
                    "input_transport_TWh": totalElecDemandInGWhForTrns[i],
                    "Input_Size_transport_electric_cars": numberOfEVCars[i],
                }
            for i in range(x.shape[0])]
        )

        # Parse the output file and store the objective function value in an
        # array
        z = self.energyplan.read_values(
            "CO2-emission (total)",
            "Variable costs",
            "Fixed operation costs",
            "Annual Investment costs",
            ("Annual", "Hydro Electr."),
            ("Annual", "PV Electr."),
            ("Annual", "Import Electr."),
            ("Annual", "Export Electr."),
            ("Annual", "HH-CHP Electr."),
            "Biomass Consumption"
        )

        # Retrieve:
        CO2 = 0         # local CO2 emissions
        VAR_COST = 1    # total variable cost
        FIX_COST = 2    # fixed operational cost
        INV_COST = 3    # investment cost
        HYDRO = 4       # annual hydropower
        PV = 5          # annual PV electricity
        IMPORT = 6      # annual import
        EXPORT = 7      # annual export
        HH_CHP = 8      # annual HH electricity CHP
        BIOMASS = 9     # annual biomass consumption

        # Compute the first objective: local CO2 emissions

        # Breakdown import electricity cost
        co2InImportedEleCoal = z[:, IMPORT] * self.scenario["coalShare"] / \
            100 * self.scenario["co2Coal"] * 3600 / 1e6
        co2InImportedEleOil = z[:, IMPORT] * self.scenario["oilShare"] / \
            100 * self.scenario["co2Oil"] * 3600 / 1e6
        co2InImportedEleNGas = z[:, IMPORT] * self.scenario["nGasShare"] / \
            100 * self.scenario["co2NGas"] * 3600 / 1e6

        # Calculate local CO2 emissions
        locaCO2Emission = z[:, CO2] + co2InImportedEleCoal + \
            co2InImportedEleOil + co2InImportedEleNGas

        # Compute the second objective: additional cost

        totalAdditionalCost = \
            (z[:, HYDRO] + z[:, PV] + z[:, IMPORT] - z[:, EXPORT] + \
             z[:, HH_CHP]) * self.scenario["additionalCostPerGWhinKEuro"]

        actualAnnualCost = z[:, VAR_COST] + z[:, FIX_COST] + z[:, INV_COST] + \
            totalAdditionalCost

        # Set objectives
        out["F"] = np.column_stack([locaCO2Emission, actualAnnualCost])

        # CONSTRAINTS

        out["G"] = np.column_stack([
            z[:, BIOMASS] - 98.84,
        ])
