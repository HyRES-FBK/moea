import numpy as np
import pandas as pd
from pathlib import Path
from pymoo.core.variable import Integer, Real


from moea.models.base_model import BaseModel
from moea.utils import (dump_input, find_values, execute_energyplan_spool,
                        parse_output)
from moea.config import ENERGYPLAN_RESULTS

"""
QUESTIONS
- What is the meaning of wave power? There are three in the output files and it
    is not clear which one to use. When, the last objective function is computed,
    the wave power is referred to as 'Biomass'
"""

class GiudicarieEsteriori(BaseModel):

    # The 
    PVInvestmentCostInKEuro = 2.6
    hydroInvestmentCostInKEuro = 1.9
    individualBoilerInvestmentCostInKEuro = 0.588
    BiogasInvestmentCostInKEuro = 4.0
    interest = 0.04

    currentPVCapacity = 7514
    currentHydroCapacity = 4000
    currentBiogasCapacity = 500
    currentIndvBiomassBoilerCapacity = 14306
    currentIndvOilBoilerCapacity = 9155
    currentIndvLPGBoilerCapacity = 3431

    totalHeatDemand = 55.82

    boilerLifeTime = 15
    PVLifeTime = 30
    HydroLifeTime = 50
    BiogasLifeTime = 20
    geoBoreHoleLifeTime = 100

    COP = 3.2

    maxHeatDemandInDistribution = 1.0
    sumOfAllHeatDistributions = 3112.94

    geoBoreholeCostInKWe = 3.2

    oilBoilerEfficiency = 0.80
    ngasBoilerEfficiency = 0.90
    biomassBoilerEfficiency = 0.75

    addtionalCostPerGWhinKEuro = 106.27

    PVPEF = 1.0
    HYPEF = 1.0
    BioGasPEF = 1/0.262
    BiomassPEF = 1/0.18
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
            "input_RES1_capacity": {"lb": 5000, "ub": 42000},  # PV capacity
            "input_fuel_Households[2]": {"lb": 0, "ub": 1},  # Oil boiler heat %
            "input_fuel_Households[3]": {"lb": 0, "ub": 1},  # Ngas boiler heat %
            "input_fuel_Households[4]": {"lb": 0, "ub": 1},  # Biomass boiler heat
            "input_HH_BioCHP_heat": {"lb": 0, "ub": 1},  # Biomass micro-CHP heat %
            "input_HH_HP_heat": {"lb": 0, "ub": 1},  # Individual HP %
        }, dtype=float, orient='index')
        
        super().__init__(
            n_var=len(self.vars),
            n_obj=4,
            xl=self.vars['lb'].values,
            xu=self.vars['ub'].values,
            data_file=data_file,
            **kwargs
        )

    def _evaluate(self, x, out, *args, **kwargs):
        # Use enums for the percentage variables
        PV = 0
        OIL = 1
        LPG = 2
        BIOMASS = 3
        CHP = 4
        HP = 5

        z = np.sort(x[:, OIL:]).T

        percentages = np.zeros_like(x.T)
        percentages[PV] = x[:, PV]
        percentages[OIL] = z[OIL]
        percentages[LPG] = z[LPG] - z[OIL]
        percentages[BIOMASS] = z[BIOMASS] - z[LPG]
        percentages[CHP] = z[CHP] - z[BIOMASS]
        percentages[HP] = 1 - z[CHP]

        # Dump the input vectors to files
        for i, ind in enumerate(percentages.T):
            dump_input({k: v for k, v in zip(self.vars.index, ind)},
                       i, self.default_data)

        # Compute the objective functions
        execute_energyplan_spool([f"input{i}.txt" for i in range(len(x))])

        # Retrieve CO2 emissions and total annual costs
        co2, variable_cost, operations_cost = find_values(
            ENERGYPLAN_RESULTS,
            "CO2-emission (corrected)",
            "Variable costs",
            "Fixed operation costs"
        ).T

        # Retrieve:
        PV = 0  # annual PV electricity
        HYDRO = 1  # annual hydropower
        WAVE = 2  # annual wave power
        IMPORT = 3  # annual import
        EXPORT = 4  # annual export
        HP = 5  # annual HP electricity
        HH_CHP = 6  # annual HH electricity CHP
        DEMAND = 7  # annual demand
        NGAS = 8  # annual natural gas
        OIL = 9  # annual oil
        BIOGAS = 10  # annual biomass

        z = np.zeros((11, len(x)))

        for i, res in enumerate(ENERGYPLAN_RESULTS.glob("*.txt")):
            D = parse_output(res)
            annual_lbl = [i for i in D.keys() if 'TOTAL FOR ONE YEAR' in i][0]
            fuel_lbl = [i for i in D.keys() if 'ANNUAL FUEL' in i][0]
            z[HYDRO, i] = float(D[annual_lbl]["Hydro Electr."])
            z[PV, i] = float(D[annual_lbl]["PV Electr."])
            z[WAVE, i] = float(max(D[annual_lbl]["Wave Electr."]))
            z[IMPORT, i] = float(D[annual_lbl]["Import Electr."])
            z[EXPORT, i] = float(D[annual_lbl]["Export Electr."])
            z[HH_CHP, i] = float(D[annual_lbl]["HH-CHP Electr."])
            z[HP, i] = float(D[annual_lbl]["HH-HP Electr."])
            z[DEMAND, i] = float(D[annual_lbl]["Electr. Demand"])
            z[NGAS, i] = float(D[fuel_lbl]['TOTAL']["Ngas Consumption"])
            z[OIL, i] = float(D[fuel_lbl]['TOTAL']["Oil Consumption"])
            z[BIOGAS, i] = float(D[fuel_lbl]['TOTAL']["Biomass Consumption"])

        total_additional_cost = (
            z[HYDRO] + z[PV] + z[WAVE] + z[HH_CHP] + z[IMPORT] - z[EXPORT]
        ) * self.addtionalCostPerGWhinKEuro

        HP_capacity = (self.maxHeatDemandInDistribution * percentages[HP] *
                       self.totalHeatDemand * 1e6) / \
                        (self.COP * self.sumOfAllHeatDistributions)

        geo_borehole_cost = (HP_capacity * self.geoBoreholeCostInKWe) / \
            (1 - (1 + self.interest) ** -self.geoBoreHoleLifeTime)

        biomass_boiler_capacity = \
            (self.totalHeatDemand * percentages[BIOMASS]) * \
                1e6 * 1.5 / self.sumOfAllHeatDistributions

        investment_cost_reduction_biomass_boiler = np.where(
            biomass_boiler_capacity > self.currentIndvBiomassBoilerCapacity,
            (self.currentIndvBiomassBoilerCapacity * \
                self.individualBoilerInvestmentCostInKEuro * \
                    self.interest) / \
                    (1 - (1 + self.interest) ** -self.boilerLifeTime),
            (biomass_boiler_capacity * \
                self.individualBoilerInvestmentCostInKEuro * \
                    self.interest) / \
                        (1 - (1 + self.interest) ** -self.boilerLifeTime)
        )

        # Since OIL has been overwritten, we use directly the index 1 for OIL
        oil_boiler_capacity = (self.totalHeatDemand * percentages[1]) * \
            1e6 * 1.5 / self.sumOfAllHeatDistributions

        investment_cost_reduction_oil_boiler = np.where(
            oil_boiler_capacity > self.currentIndvOilBoilerCapacity,
            (self.currentIndvOilBoilerCapacity * \
                self.individualBoilerInvestmentCostInKEuro * \
                    self.interest) / \
                    (1 - (1 + self.interest) ** -self.boilerLifeTime),
            (oil_boiler_capacity * \
                self.individualBoilerInvestmentCostInKEuro * \
                    self.interest) / \
                        (1 - (1 + self.interest) ** -self.boilerLifeTime)
        )

        lpg_boiler_capacity = (self.totalHeatDemand * percentages[LPG]) * \
            1e6 * 1.5 / self.sumOfAllHeatDistributions
        
        investment_cost_reduction_lpg_boiler = np.where(
            lpg_boiler_capacity > self.currentIndvLPGBoilerCapacity,
            (self.currentIndvLPGBoilerCapacity * \
                self.individualBoilerInvestmentCostInKEuro * \
                    self.interest) / \
                    (1 - (1 + self.interest) ** -self.boilerLifeTime),
            (lpg_boiler_capacity * \
                self.individualBoilerInvestmentCostInKEuro * \
                    self.interest) / \
                        (1 - (1 + self.interest) ** -self.boilerLifeTime)
        )

        reduction_investment_cost = \
            (self.currentPVCapacity * self.PVInvestmentCostInKEuro *
             self.interest) / (1 - (1 + self.interest) ** -self.PVLifeTime) + \
            (self.currentHydroCapacity * self.hydroInvestmentCostInKEuro *
             self.interest) / (1 - (1 + self.interest) ** -self.HydroLifeTime) + \
            (self.currentBiogasCapacity * self.BiogasInvestmentCostInKEuro *
             self.interest) / (1 - (1 + self.interest) ** -self.BiogasLifeTime) + \
            investment_cost_reduction_biomass_boiler + \
            investment_cost_reduction_oil_boiler + \
            investment_cost_reduction_lpg_boiler

        # Retrieve annual investment costs
        annual_investment_costs = np.reshape(find_values(
            ENERGYPLAN_RESULTS,
            "Annual Investment costs"
        ), -1)

        # Compute the real invertment cost
        real_investment_cost = annual_investment_costs - \
            reduction_investment_cost + geo_borehole_cost

        # Compute the actual annual cost, which is the third objective
        actual_annual_cost = variable_cost + operations_cost + \
            total_additional_cost + real_investment_cost

        # Individual house HP electric demand
        individual_house_HP_demand = \
            (z[IMPORT] + z[EXPORT]) / (z[DEMAND] - z[HP])
        
        total_PE_electricity = z[PV] * self.PVPEF + z[HYDRO] * self.HYPEF + \
            z[WAVE] * self.BioGasPEF + z[BIOMASS] * self.BiomassPEF

        total_local_electricity = z[PV] + z[HYDRO] + z[WAVE] + z[HH_CHP]

        total_PE_consumption = total_PE_electricity / total_local_electricity

        ESD = (z[IMPORT] * self.PEFImport + z[OIL] + z[NGAS]) / \
            total_PE_consumption

        out["F"] = np.column_stack([
            co2, actual_annual_cost, individual_house_HP_demand, ESD
        ])
