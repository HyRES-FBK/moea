import numpy as np
import pandas as pd
from pathlib import Path


from moea.models.base_model import BaseModel
from moea.energyplan.energyplan110 import EnergyPLAN110


class GiudicarieEsteriori(BaseModel):

    energyplan_version = EnergyPLAN110

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
                 data_file: str | Path = 'CEIS_Complete_Current.txt',
                 **kwargs):
        """
        The problem class replicates the model in:

        > Mahbub, Md Shahriar, Diego Viesi, and Luigi Crema (2016).
        > Designing optimized energy scenarios for an Italian Alpine valley:
        > the case of Giudicarie Esteriori. *Energy* 116, 236-249.

        """

        self.vars = pd.DataFrame.from_dict({
            "PVCapacity": {
                "lb": 5000,
                "ub": 42000,
                "dk0": True,  # Domain knowledge about renewable energy
                "dk1": False,  # Domain knowledge about conventional PP
                "dk2": False,  # Domain knowledge about load following capacity
                "dk3": True  # Domain knowledge about ESD
            },
            "oilBoilerPercentage": {
                "lb": 0,
                "ub": 1,
                "dk0": False,
                "dk1": None,
                "dk2": None,
                "dk3": False
            },
            "LPGBoilerPercentage": {
                "lb": 0,
                "ub": 1,
                "dk0": None,
                "dk1": None,
                "dk2": None,
                "dk3": False
            },
            "biomassBoilerPercentage": {
                "lb": 0,
                "ub": 1,
                "dk0": True,
                "dk1": True,
                "dk2": None,
                "dk3": True
            },
            "biomassCHP": {
                "lb": 0,
                "ub": 1,
                "dk0": True,
                "dk1": False,
                "dk2": True,
                "dk3": True
            },
            "electricCarPercentage": {
                "lb": 0,
                "ub": 1,
                "dk0": True,
                "dk1": False,
                "dk2": None,
                "dk3": True
            },
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

    def _evaluate(self, x, out):

        pv = x[:, 0]

        percentages = np.copy(x[:, 1:self.n_var - 1])
        percentages = np.sort(percentages, axis=1)
        oilBoilerHeatPercentage = percentages[:, 0]
        LPGBoilerHeatPercentage = percentages[:, 1] - percentages[:, 0]
        biomassBoilerHeatPercentage = percentages[:, 2] -percentages[:, 1]
        biomassCHPHeatPercentage = percentages[:, 3] - percentages[:, 2]
        hpHeatPercentage = 1 - percentages[:, 3]

        # Electric car percentage
        electricCarPercentage = x[:, -1]
        reducedNumberOfPetrolCars = (self.currentNumberOfPertrolCars * \
            (1 - electricCarPercentage)).astype(int)
        reducedNumberOfDieselCars = (self.currentNumberOfDieselCars * \
            (1 - electricCarPercentage)).astype(int)
        reducedPetrolDemandInGWh = \
            (reducedNumberOfPetrolCars * self.averageKMPerYearForPetrolCar * \
             self.LCVPetrol) / (self.petrolCarRunsKMperL * 1000000)
        reducedDieselDemandInGWh = \
            (reducedNumberOfDieselCars * self.averageKMPerYearForDieselCar * \
                self.LCVDiesel) / (self.DieselCarRunsKMperL * 1000000)
        elecCarRunKM = self.totalKMRunByCars - \
            (reducedNumberOfPetrolCars * self.averageKMPerYearForPetrolCar) - \
                (reducedNumberOfDieselCars * self.averageKMPerYearForDieselCar)
        elecCarElectricityDemandInGWh = elecCarRunKM * \
            self.KWhPerKMElecCar / 1000000

        oilBoilerFuelDemand = self.totalHeatDemand * oilBoilerHeatPercentage \
            / self.oilBoilerEfficiency
        LPGBoilerDemand = self.totalHeatDemand * LPGBoilerHeatPercentage / \
            self.ngasBoilerEfficiency
        biogasBoilerDemand = self.totalHeatDemand * \
            biomassBoilerHeatPercentage / self.biomassBoilerEfficiency
        bioCHPDemand = self.totalHeatDemand * biomassCHPHeatPercentage
        HPDemand = self.totalHeatDemand * hpHeatPercentage

        self.energyplan.run(
            inputs=[{
                "input_RES1_capacity": int(pv[i]),
                "input_fuel_Households[2]": oilBoilerFuelDemand[i],
                "input_fuel_Households[3]": LPGBoilerDemand[i],
                "input_fuel_Households[4]": biogasBoilerDemand[i],
                "input_HH_BioCHP_heat": bioCHPDemand[i],
                "input_HH_HP_heat": HPDemand[i],
                "input_transport_TWh": elecCarElectricityDemandInGWh[i],
                "input_fuel_Transport[2]": "{:.2f}".format(reducedDieselDemandInGWh[i]),
                "input_fuel_Transport[5]": "{:.2f}".format(reducedPetrolDemandInGWh[i]),
                "Filnavn_transport": "CIVIS_Transport_NC.txt"
            } for i in range(x.shape[0])]
        )

        # Retrieve CO2 emissions and total annual costs
        z = self.energyplan.read_values(
                "CO2-emission (corrected)",
                "Total variable costs",
                "Fixed operation costs",
                "Annual Investment costs",
                ("Annual", "Hydro power"),
                ("Annual", "PV"),
                ("Annual", "Wave power"),
                ("Annual", "import"),
                ("Annual", "export"),
                ("Annual", "HH-elec. CHP"),
                ("Annual", "HH-elec. HP"),
                ("Annual", "elec. demand"),
                "Ngas Consumption",
                "Oil Consumption",
                "Biomass Consumption",
                ("Annual", "flexible eldemand")
            )

        # Retrieve:
        CO2 = 0         # annual CO2 emissions
        VAR_COST = 1    # annual variable costs
        FIX_COST = 2    # annual fixed costs
        INV_COST = 3    # annual investment costs
        HYDRO = 4       # annual hydropower
        PV = 5          # annual PV electricity
        WAVE = 6        # annual wave power
        IMPORT = 7      # annual import
        EXPORT = 8      # annual export
        HH_CHP = 9      # annual HH electricity CHP

        HP = 10         # annual HP electricity
        DEMAND = 11     # annual demand
        NGAS = 12       # annual natural gas
        OIL = 13        # annual oil
        BIOMASS = 14    # annual biomass
        FLEXI = 15      # annual flexible demand

        totalAdditionalCost = ((
            z[:, HYDRO] + z[:, PV] + z[:, HH_CHP] + z[:, IMPORT] - z[:, EXPORT]
        ) * self.addtionalCostPerGWhinKEuro).astype(int)

        # The meaning of HP changed, use directly the index 4
        capacityOfHeatPump = (
            (self.maxHeatDemandInDistribution * hpHeatPercentage *
             self.totalHeatDemand * 1e6) / \
                (self.COP * self.sumOfAllHeatDistributions)).astype(int)

        geoBoreHoleInvestmentCost = (
            capacityOfHeatPump * self.geoBoreholeCostInKWe * self.interest
        ) / (1 - np.pow((1 + self.interest), -self.geoBoreHoleLifeTime))

        # See the annual inventment cost formula in EnergyPLAN manual

        # The meaning of BIOMASS changed, use directly the index 2
        newCapacityBiomassBoiler = (
            (self.totalHeatDemand * biomassBoilerHeatPercentage) * 1e6 * 1.5 /
            self.sumOfAllHeatDistributions).astype(int)

        investmentCostReductionBiomassBoiler = np.where(
            newCapacityBiomassBoiler > self.currentIndvBiomassBoilerCapacity,
            (self.currentIndvBiomassBoilerCapacity * \
                self.individualBoilerInvestmentCostInKEuro * \
                    self.interest) / \
                    (1 - np.pow((1 + self.interest), -self.boilerLifeTime)),
            (newCapacityBiomassBoiler * \
                self.individualBoilerInvestmentCostInKEuro * \
                    self.interest) / \
                        (1 - np.pow((1 + self.interest), -self.boilerLifeTime))
        )

        # Since OIL has been overwritten, we use directly the index 1 for OIL
        newCapacityOilBoiler = (
            (self.totalHeatDemand * oilBoilerHeatPercentage) *
            1e6 * 1.5 / self.sumOfAllHeatDistributions).astype(int)

        investmentCostReductionOilBoiler = np.where(
            newCapacityOilBoiler > self.currentIndvOilBoilerCapacity,
            (self.currentIndvOilBoilerCapacity * \
                self.individualBoilerInvestmentCostInKEuro * \
                    self.interest) / \
                    (1 - np.pow((1 + self.interest), -self.boilerLifeTime)),
            (newCapacityOilBoiler * \
                self.individualBoilerInvestmentCostInKEuro * \
                    self.interest) / \
                        (1 - np.pow((1 + self.interest), -self.boilerLifeTime))
        )

        # Since LPG has been overwritten, we use directly the index 1 for LPG
        newCapacityLPGBoiler = (
            (self.totalHeatDemand * LPGBoilerHeatPercentage) *
            1e6 * 1.5 / self.sumOfAllHeatDistributions).astype(int)

        investmentCostReductionLPGBoiler = np.where(
            newCapacityLPGBoiler > self.currentIndvLPGBoilerCapacity,
            (self.currentIndvLPGBoilerCapacity * \
                self.individualBoilerInvestmentCostInKEuro * \
                    self.interest) / \
                    (1 - np.pow((1 + self.interest), -self.boilerLifeTime)),
            (newCapacityLPGBoiler * \
                self.individualBoilerInvestmentCostInKEuro * \
                    self.interest) / \
                        (1 - np.pow((1 + self.interest), -self.boilerLifeTime))
        )

        reductionInvestmentCost = \
            (self.currentPVCapacity * self.PVInvestmentCostInKEuro *
             self.interest) / (1 - np.pow((1 + self.interest), -self.PVLifeTime)) + \
            (self.currentHydroCapacity * self.hydroInvestmentCostInKEuro *
             self.interest) / \
                (1 - np.pow((1 + self.interest), -self.HydroLifeTime)) + \
            (self.currentBiogasCapacity * self.BiogasInvestmentCostInKEuro *
             self.interest) / \
                (1 - np.pow((1 + self.interest), -self.BiogasLifeTime)) + \
            investmentCostReductionBiomassBoiler + \
            investmentCostReductionOilBoiler + \
            investmentCostReductionLPGBoiler

        # Compute the real investment cost
        realInvestmentCost = z[:, INV_COST] - \
            reductionInvestmentCost + geoBoreHoleInvestmentCost

        # Electric car related costs
        totalNumberOfELectricCars = (
            self.currentNumberOfPertrolCars + self.currentNumberOfDieselCars -
            reducedNumberOfPetrolCars - reducedNumberOfDieselCars).astype(int)

        totalInvestmentCostForElectricCars = (totalNumberOfELectricCars * \
            self.costOfElectricCarInKeuro * self.interest) / \
                (1 - np.pow((1 + self.interest), -self.electricCarLifeTime))

        totalFixOperationalAndInvestmentCostForElectricCars = \
            totalNumberOfELectricCars * self.costOfElectricCarInKeuro * \
                self.electricCarOperationalAndMaintanenceCost

        # Compute the actual annual cost, which is the third objective
        actualAnnualCost = z[:, VAR_COST] + z[:, FIX_COST] + \
            realInvestmentCost + totalAdditionalCost + \
            totalInvestmentCostForElectricCars + \
                totalFixOperationalAndInvestmentCostForElectricCars

        # Load followint capacity
        LFS = (z[:, IMPORT] + z[:, EXPORT]) / \
            (z[:, DEMAND] + z[:, FLEXI] + z[:, HP])

        totalPEForElectricity = z[:, PV] * self.PVPEF + z[:, HYDRO] * self.HYPEF + \
            z[:, WAVE] * self.BioGasPEF + z[:, BIOMASS] * self.BiomassPEF

        totalLocalElecProduction = z[:, PV] + z[:, HYDRO] + z[:, WAVE] + z[:, HH_CHP]

        PEFLocalElec = totalPEForElectricity / totalLocalElecProduction

        totalPEConsumption = (totalLocalElecProduction - z[:, EXPORT]) * \
            PEFLocalElec + z[:, IMPORT] * self.PEFImport + z[:, BIOMASS] + \
                z[:, OIL] + z[:, NGAS] + (self.totalHeatDemand * hpHeatPercentage) * \
                    (1 - 1 / self.COP)

        ESD = (z[:, IMPORT] * self.PEFImport + z[:, OIL] + z[:, NGAS]) / \
            totalPEConsumption

        out["F"] = np.column_stack([
            z[:, CO2], actualAnnualCost, LFS, ESD
        ])

        ##########################
        # Evaluate the constraints
        ##########################
        # There is only one constraint to limit the consumption of biomass
        out["G"] = np.column_stack([56.87 - z[:, BIOMASS]])
