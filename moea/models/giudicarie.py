import numpy as np
import pandas as pd
from pathlib import Path


from moea.models.base_model import BaseModel
from moea.utils import dump_input, find_values, execute_energyplan_spool
from moea.config import ENERGYPLAN_RESULTS


class GiudicarieEsteriori(BaseModel):

    # Investment costs in kEuro
    PVInvestmentCostInKEuro = 2.6
    hydroInvestmentCostInKEuro = 1.9
    individualBoilerInvestmentCostInKEuro = 0.588
    BiogasInvestmentCostInKEuro = 4.0

    # Interest rate
    interest = 0.04

    # Current capacities in kW
    currentPVCapacity = 7514
    currentHydroCapacity = 4000
    currentBiogasCapacity = 500
    currentIndvBiomassBoilerCapacity = 14306
    currentIndvOilBoilerCapacity = 9155
    currentIndvLPGBoilerCapacity = 3431

    # Total heat demand in GWh
    totalHeatDemand = 55.82

    # Lifetimes in years
    boilerLifeTime = 15
    PVLifeTime = 30
    HydroLifeTime = 50
    BiogasLifeTime = 20
    geoBoreHoleLifeTime = 100

    # COP
    COP = 3.2

    maxHeatDemandInDistribution = 1.0
    sumOfAllHeatDistributions = 3112.94

    geoBoreholeCostInKWe = 3.2

    # Boiler efficiencies
    oilBoilerEfficiency = 0.80
    ngasBoilerEfficiency = 0.90
    biomassBoilerEfficiency = 0.75

    # Additional costs in kEuro/GWh
    addtionalCostPerGWhinKEuro = 106.27

	# Transport related data
    currentNumberOfPertrolCars = 2762
    currentNumberOfDieselCars = 2094
    averageKMPerYearForPetrolCar = 7250
    averageKMPerYearForDieselCar = 13400

    # lower calorific value (LCV): KWh/l
    # (ref: http://www.withouthotair.com/c3/page_31.shtml) check with Diego
    LCVPetrol = 8.86
    LCVDiesel = 10.12
    KWhPerKMElecCar = 0.168
    petrolCarRunsKMperL = 15.5
    DieselCarRunsKMperL = 18.2
    totalKMRunByCars = 48084100
    costOfElectricCarInKeuro = 18.690
    electricCarLifeTime = 15
    # 5.5 percent of Investment cost (costOfElectricCarInKeuro)
    electricCarOperationalAndMaintanenceCost = 0.055

    PVPEF = 1.0
    HYPEF = 1.0
    BioGasPEF = 1 / 0.262
    BiomassPEF = 1 / 0.18
    PEFImport = 2.17

    def __init__(self,
                 data_file: str | Path = 'CEISCompleteCurrent.txt',
                 **kwargs):
        """
        The problem class replicates the model in:

        > Mahbub, Md Shahriar, Diego Viesi, and Luigi Crema (2016).
        > Designing optimized energy scenarios for an Italian Alpine valley:
        > the case of Giudicarie Esteriori. *Energy* 116, 236-249.

        """

        self.vars = pd.DataFrame.from_dict({
            "PVCapacity": {"lb": 5000, "ub": 42000},        # PV capacity
            "oilBoilerPercentage": {"lb": 0, "ub": 1},      # Oil boiler heat %
            "LPGBoilerPercentage": {"lb": 0, "ub": 1},      # LPG boiler heat %
            "biomassBoilerPercentage": {"lb": 0, "ub": 1},  # Biomass boiler heat
            "biomassCHP": {"lb": 0, "ub": 1},               # Biomass micro-CHP heat %
            "electricCarPercentage": {"lb": 0, "ub": 1},    # Electric car %
        }, dtype=float, orient='index')

        super().__init__(
            n_var=len(self.vars),
            n_obj=4,
            n_ieq_constr=1,
            xl=self.vars['lb'].values,
            xu=self.vars['ub'].values,
            data_file=data_file,
            **kwargs
        )

    def _evaluate(self, x, out, *args, **kwargs):
        # Use pseudo-enums
        OIL = 0
        LPG = 1
        BIOMASS = 2
        CHP = 3
        HP = 4
        EC = 5

        # Sort percentages in ascending order
        sorted_perc = np.sort(x[:, 1:]).T

        percentages = np.zeros((5, len(x)))
        percentages[OIL] = sorted_perc[OIL]
        percentages[LPG] = sorted_perc[LPG] - sorted_perc[OIL]
        percentages[BIOMASS] = sorted_perc[BIOMASS] - sorted_perc[LPG]
        percentages[CHP] = sorted_perc[CHP] - sorted_perc[BIOMASS]
        percentages[HP] = 1 - sorted_perc[CHP]

        # Electric car percentage
        reducedNumberOfPetrolCars = (self.currentNumberOfPertrolCars * \
            (1 - x[:, EC])).astype(int)
        reducedNumberOfDieselCars = (self.currentNumberOfDieselCars * \
            (1 - x[:, EC])).astype(int)
        reducedPetrolDemandInGWh = \
            (reducedNumberOfPetrolCars * self.averageKMPerYearForPetrolCar * \
             self.LCVPetrol) / (self.petrolCarRunsKMperL * 1e6)
        reducedDieselDemandInGWh = \
            (reducedNumberOfDieselCars * self.averageKMPerYearForDieselCar * \
                self.LCVDiesel) / (self.DieselCarRunsKMperL * 1e6)
        elecCarRunKM = self.totalKMRunByCars - \
            (reducedNumberOfPetrolCars * self.averageKMPerYearForPetrolCar) - \
                (reducedNumberOfDieselCars * self.averageKMPerYearForDieselCar)
        elecCarElectricityDemandInGWh = elecCarRunKM * \
            self.KWhPerKMElecCar / 1e6

        oilBoilerDemand = self.totalHeatDemand * percentages[OIL] / \
            self.oilBoilerEfficiency
        LPGBoilerDemand = self.totalHeatDemand * percentages[LPG] / \
            self.ngasBoilerEfficiency
        biogasBoilerDemand = self.totalHeatDemand * percentages[BIOMASS] / \
            self.biomassBoilerEfficiency
        bioCHPDemand = self.totalHeatDemand * percentages[CHP]
        HPDemand = self.totalHeatDemand * percentages[HP]

        # Dump the input vectors to files
        for i, ind in enumerate(x):
            dump_input(
                {
                    "input_RES1_capacity": ind[0],
                    "input_fuel_Households[2]": oilBoilerDemand[i],
                    "input_fuel_Households[3]": LPGBoilerDemand[i],
                    "input_fuel_Households[4]": biogasBoilerDemand[i],
                    "input_HH_BioCHP_heat": bioCHPDemand[i],
                    "input_HH_HP_heat": HPDemand[i],
                    "input_transport_TWh": elecCarElectricityDemandInGWh[i],
                    "input_fuel_Transport[2]": reducedDieselDemandInGWh[i],
                    "input_fuel_Transport[5]": reducedPetrolDemandInGWh[i],
                    "Filnavn_transport": "CIVIS_Transport_NC.txt"
                },
                i, self.default_data)

        # Compute the objective functions
        execute_energyplan_spool([f"input{i}.txt" for i in range(len(x))])

        # Retrieve CO2 emissions and total annual costs
        z = find_values(
                ENERGYPLAN_RESULTS,
                "CO2-emission (corrected)",
                "Variable costs",
                "Fixed operation costs",
                "Annual Investment costs",
                ("Annual", "Hydro Electr."),
                ("Annual", "PV Electr."),
                ("Annual", "Wave Electr."),
                ("Annual", "Import Electr."),
                ("Annual", "Export Electr."),
                ("Annual", "HH-CHP Electr."),
                ("Annual", "HH-HP Electr."),
                ("Annual", "Electr. Demand"),
                "Ngas Consumption",
                "Oil Consumption",
                "Biomass Consumption",
                ("Annual", "Flexible Electr.")
            ).T

        # Retrieve:
        CO2 = 0  # annual CO2 emissions
        VAR_COST = 1  # annual variable costs
        FIX_COST = 2  # annual fixed costs
        INV_COST = 3  # annual investment costs
        PV = 3  # annual PV electricity
        HYDRO = 4  # annual hydropower
        WAVE = 5  # annual wave power
        IMPORT = 6  # annual import
        EXPORT = 7  # annual export
        HP = 8  # annual HP electricity
        HH_CHP = 9  # annual HH electricity CHP
        DEMAND = 10  # annual demand
        NGAS = 11  # annual natural gas
        OIL = 12  # annual oil
        BIOMASS = 13  # annual biomass
        FLEXI = 14  # annual flexible demand

        totalAdditionalCost = ((
            z[HYDRO] + z[PV] + z[HH_CHP] + z[IMPORT] - z[EXPORT]
        ) * self.addtionalCostPerGWhinKEuro).astype(int)

        # The meaning of HP changed, use directly the index 4
        capacityOfHeatPump = (
            (self.maxHeatDemandInDistribution * percentages[4] *
             self.totalHeatDemand * 1e6) / \
                (self.COP * self.sumOfAllHeatDistributions)).astype(int)

        geoBoreHoleInvestmentCost = (
            capacityOfHeatPump * self.geoBoreholeCostInKWe * self.interest
        ) / (1 - (1 + self.interest) ** -self.geoBoreHoleLifeTime)

        # See the annual inventment cost formula in EnergyPLAN manual

        # The meaning of BIOMASS changed, use directly the index 2
        newCapacityBiomassBoiler = (
            (self.totalHeatDemand * percentages[2]) * 1e6 * 1.5 /
            self.sumOfAllHeatDistributions).astype(int)

        investmentCostReductionBiomassBoiler = np.where(
            newCapacityBiomassBoiler > self.currentIndvBiomassBoilerCapacity,
            (self.currentIndvBiomassBoilerCapacity * \
                self.individualBoilerInvestmentCostInKEuro * \
                    self.interest) / \
                    (1 - (1 + self.interest) ** -self.boilerLifeTime),
            (newCapacityBiomassBoiler * \
                self.individualBoilerInvestmentCostInKEuro * \
                    self.interest) / \
                        (1 - (1 + self.interest) ** -self.boilerLifeTime)
        )

        # Since OIL has been overwritten, we use directly the index 1 for OIL
        newCapacityOilBoiler = ((self.totalHeatDemand * percentages[1]) * \
            1e6 * 1.5 / self.sumOfAllHeatDistributions).astype(int)

        investmentCostReductionOilBoiler = np.where(
            newCapacityOilBoiler > self.currentIndvOilBoilerCapacity,
            (self.currentIndvOilBoilerCapacity * \
                self.individualBoilerInvestmentCostInKEuro * \
                    self.interest) / \
                    (1 - (1 + self.interest) ** -self.boilerLifeTime),
            (newCapacityOilBoiler * \
                self.individualBoilerInvestmentCostInKEuro * \
                    self.interest) / \
                        (1 - (1 + self.interest) ** -self.boilerLifeTime)
        )

        # Since LPG has been overwritten, we use directly the index 1 for LPG
        newCapacityLPGBoiler = ((self.totalHeatDemand * percentages[1]) * \
            1e6 * 1.5 / self.sumOfAllHeatDistributions).astype(int)

        investmentCostReductionLPGBoiler = np.where(
            newCapacityLPGBoiler > self.currentIndvLPGBoilerCapacity,
            (self.currentIndvLPGBoilerCapacity * \
                self.individualBoilerInvestmentCostInKEuro * \
                    self.interest) / \
                    (1 - (1 + self.interest) ** -self.boilerLifeTime),
            (newCapacityLPGBoiler * \
                self.individualBoilerInvestmentCostInKEuro * \
                    self.interest) / \
                        (1 - (1 + self.interest) ** -self.boilerLifeTime)
        )

        reductionInvestmentCost = \
            (self.currentPVCapacity * self.PVInvestmentCostInKEuro *
             self.interest) / (1 - (1 + self.interest) ** -self.PVLifeTime) + \
            (self.currentHydroCapacity * self.hydroInvestmentCostInKEuro *
             self.interest) / \
                (1 - (1 + self.interest) ** -self.HydroLifeTime) + \
            (self.currentBiogasCapacity * self.BiogasInvestmentCostInKEuro *
             self.interest) / \
                (1 - (1 + self.interest) ** -self.BiogasLifeTime) + \
            investmentCostReductionBiomassBoiler + \
            investmentCostReductionOilBoiler + \
            investmentCostReductionLPGBoiler

        # Compute the real investment cost
        realInvestmentCost = z[INV_COST] - \
            reductionInvestmentCost + geoBoreHoleInvestmentCost

        # Electric car related costs
        totalNumberOfELectricCars = (
            self.currentNumberOfPertrolCars + self.currentNumberOfDieselCars -
            reducedNumberOfPetrolCars - reducedNumberOfDieselCars).astype(int)

        totalInvestmentCostForElectricCars = totalNumberOfELectricCars * \
            self.costOfElectricCarInKeuro * self.interest / \
                (1 - (1 + self.interest) ** -self.electricCarLifeTime)

        totalFixOperationalAndInvestmentCostForElectricCars = \
            totalNumberOfELectricCars * self.costOfElectricCarInKeuro * \
                self.electricCarOperationalAndMaintanenceCost

        # Compute the actual annual cost, which is the third objective
        actualAnnualCost = z[VAR_COST] + z[FIX_COST] + \
            realInvestmentCost + totalAdditionalCost + \
            totalInvestmentCostForElectricCars + \
                totalFixOperationalAndInvestmentCostForElectricCars

        # Load followint capacity
        LFS = (z[IMPORT] + z[EXPORT]) / (z[DEMAND] + z[FLEXI] + z[HP])

        totalPEForElectricity = z[PV] * self.PVPEF + z[HYDRO] * self.HYPEF + \
            z[WAVE] * self.BioGasPEF + z[BIOMASS] * self.BiomassPEF

        totalLocalElecProduction = z[PV] + z[HYDRO] + z[WAVE] + z[HH_CHP]

        PEFLocalElec = totalPEForElectricity / totalLocalElecProduction

        totalPEConsumption = (totalLocalElecProduction - z[EXPORT]) * \
            PEFLocalElec + z[IMPORT] * self.PEFImport + z[BIOMASS] + \
                z[OIL] + z[NGAS] + (self.totalHeatDemand * percentages[4]) * \
                    (1 - 1 / self.COP)

        ESD = (z[IMPORT] * self.PEFImport + z[OIL] + z[NGAS]) / \
            totalPEConsumption

        out["F"] = np.column_stack([
            z[CO2], actualAnnualCost, LFS, ESD
        ])

        ##########################
        # Evaluate the constraints
        ##########################
        # There is only one constraint to limit the consumption of biomass
        out["G"] = np.column_stack([56.87 - z[BIOMASS]])
