import numpy as np
import pandas as pd
from typing import Union
from pathlib import Path


from moea.utils import (dump_input, find_values, execute_energyplan_spool,
                        parse_output)
from moea.config import ENERGYPLAN_RESULTS, logger
from moea.models.base_model import BaseModel


class ValDiNon(BaseModel):
    """
    This problem class replicates the model in {cite:ps}`MAHBUB20171487`.

    The problem implementation refers [this implementation]
    (https://github.com/shaikatcse/EnergyPLANDomainKnowledgeEAStep1/blob/master/src/reet/fbk/eu/OptimizeEnergyPLANVdN/problem/EnergyPLANProblemVdN2DWithElecVehicleModifiedCO2.java)
    by Mahbub's.

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
	# Common data for all scenarios
	# CO2 content related data

    def __init__(self,
                 year: int,
                 scenario: dict = None,
                 data_file: Union[str, Path] = "VdN_SH_2008.txt",
                 **kwargs):
        """
        Parameters:
        -----------
        - ``year``: int

            The year of the scenario.

        - ``scenario``: dict

            A dictionary containing the scenario data. The dictionary should
            have the following keys:
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
        # Set the scenario
        self.scenario = scenario

        # If no scenario is provided, use the default one
        if self.scenario is None:
            logger.warning("No scenario provided. Using the default one.")
            self.scenario = pd.read_csv('docs/use-cases/vdn-scenarios.csv',
                                        index_col=0)["2020"].to_dict()

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
        # Use index naming
        PV = 0
        OIL = 1
        NGAS = 2
        BIOMASS = 3
        MICROCHP = 4
        EV = 5
        OILSOLAR = 6
        NGASSOLAR = 7
        BIOMASSSOLAR = 8
        MICROCHPSOLAR = 9
        HEATSOLAR = 10

        # Heat percentages
        heatPercentages = np.sort(x.T[OIL:EV], axis=1)

        oilBoilerPercentage = heatPercentages[OIL - 1]
        nGasBoilerPercentage = heatPercentages[NGAS - 1] - \
            heatPercentages[OIL - 1]
        biomassBoilerPercentage = heatPercentages[BIOMASS - 1] - \
            heatPercentages[NGAS - 1]
        biomassMicroCHPPercentage = heatPercentages[MICROCHP - 1] - \
            heatPercentages[BIOMASS - 1]
        heatPumpPercentage = 1 - heatPercentages[MICROCHP - 1]

        # Electric car percentage
        EVCarPercentage = x.T[EV]
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
        oilSolarPercentage = x.T[OILSOLAR]
        nGasSolarPercentage = x.T[NGASSOLAR]
        biomassSolarPercentage = x.T[BIOMASSSOLAR]
        microCHPSolarPercentage = x.T[MICROCHPSOLAR]
        hpSolarPercentage = x.T[HEATSOLAR]

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
        biomassMicroCHPFuelDemand = biomassMicroCHPPercentage * \
            self.scenario["totalHeatDemand"]
        biomassMicroCHPSolarThermal = biomassMicroCHPFuelDemand * \
            microCHPSolarPercentage * self.scenario["efficiencyBiomassCHP"]

        # Fuel demand for heat pump
        heatPumpFuelDemand = heatPumpPercentage * \
            self.scenario["totalHeatDemand"]
        # TODO: Check if this is correct
        heatPumpSolarThermal = heatPumpPercentage * hpSolarPercentage * \
            self.scenario["totalHeatDemand"]

        # Calculate the number of conventional cars and electric cars
        numberOfConCars = totalDieselDemandInGWhForTrns * 1e6 / \
            (self.scenario["efficiencyConCar"] *
             self.scenario["averageKMPerYearPerCar"] * 1e3)
        numberOfEVCars = totalElecDemandInGWhForTrns * 1e6 / \
            (self.scenario["efficiencyEVCar"] *
             self.scenario["averageKMPerYearPerCar"] * 1e3)

        # Iterate over individuals and create an input file for each one
        # Dump the input vector to a file
        for i, ind in enumerate(x):
            dump_input({
                "input_RES1_capacity": ind[PV].astype(int),
                "input_fuel_Households[2]": oilBoilerFuelDemand[i],
                "input_HH_oilboiler_Solar": oilSolarThermal[i],
                "input_fuel_Households[3]": nGasBoilerFuelDemand[i],
                "input_HH_ngasboiler_Solar": nGasSolarThermal[i],
                "input_fuel_Households[4]": biomassBoilerFuelDemand[i],
                "input_HH_bioboiler_Solar": biomassBoilerSolarThermal[i],
                "input_HH_BioCHP_heat": biomassMicroCHPFuelDemand[i],
                "input_HH_bioCHP_solar": biomassMicroCHPSolarThermal[i],
                "input_HH_HP_heat": heatPumpFuelDemand[i],
                "input_HH_HP_solar": heatPumpSolarThermal[i],
                "input_fuel_Transport[5]": totalDieselDemandInGWhForTrns[i],
                "Input_Size_transport_conventional_cars": numberOfConCars[i],
                "input_transport_TWh": totalElecDemandInGWhForTrns[i],
                "Input_Size_transport_electric_cars": numberOfEVCars[i],
            }, i, self.default_data)

        # Call EnergyPLAN using spool mode; only the input files are needed
        execute_energyplan_spool([f"input{i}.txt" for i in range(len(x))])

        # Parse the output file and store the objective function value in an
        # array
        (localCO2emission, totalVariableCost,
         fixedOperationalCost, investmentCost) = find_values(
            ENERGYPLAN_RESULTS,
            "CO2-emission (total)",
            "Variable costs",
            "Fixed operation costs",
            "Annual Investment costs",
        ).T

        # Retrieve:
        PV = 0  # annual PV electricity
        HYDRO = 1  # annual hydropower
        IMPORT = 2  # annual import
        EXPORT = 3  # annual export
        HH_CHP = 4  # annual HH electricity CHP
        BIOMASS = 5  # annual biomass consumption

        z = np.zeros((6, len(x)))

        for i, res in enumerate(ENERGYPLAN_RESULTS.glob("*.txt")):
            D = parse_output(res)
            annual_lbl = [i for i in D.keys() if 'TOTAL FOR ONE YEAR' in i][0]
            fuel_lbl = [i for i in D.keys() if 'ANNUAL FUEL' in i][0]
            z[HYDRO, i] = float(D[annual_lbl]["Hydro Electr."])
            z[PV, i] = float(D[annual_lbl]["PV Electr."])
            z[IMPORT, i] = float(D[annual_lbl]["Import Electr."])
            z[EXPORT, i] = float(D[annual_lbl]["Export Electr."])
            z[HH_CHP, i] = float(D[annual_lbl]["HH-CHP Electr."])
            z[BIOMASS, i] = float(D[fuel_lbl]['TOTAL']["Biomass Consumption"])

        # Compute the first objective: local CO2 emissions

        # Breakdown import electricity cost
        co2InImportedEleCoal = z[IMPORT] * self.scenario["coalShare"] / \
            100 * self.scenario["co2Coal"] * 3600 / 1e6
        co2InImportedEleOil = z[IMPORT] * self.scenario["oilShare"] / \
            100 * self.scenario["co2Oil"] * 3600 / 1e6
        co2InImportedEleNGas = z[IMPORT] * self.scenario["nGasShare"] / \
            100 * self.scenario["co2NGas"] * 3600 / 1e6

        # Calculate local CO2 emissions
        locaCO2Emission = localCO2emission + co2InImportedEleCoal + \
            co2InImportedEleOil + co2InImportedEleNGas

        # Compute the second objective: additional cost

        totalAdditionalCost = (z[HYDRO] + z[PV] + z[IMPORT] - z[EXPORT] + \
                               z[HH_CHP]) * \
            self.scenario["additionalCostPerGWhinKEuro"]

        actualAnnualCost = totalVariableCost + fixedOperationalCost + \
            investmentCost + totalAdditionalCost

        # Set objectives
        out["F"] = np.column_stack([locaCO2Emission, actualAnnualCost])

        # CONSTRAINTS

        out["G"] = np.column_stack([
            z[BIOMASS] - 98.84,
        ])
