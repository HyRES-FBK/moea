import numpy as np
from pathlib import Path
from pymoo.core.variable import Integer, Real


from moea.models.base_model import BaseModel
from moea.utils import (dump_input, find_values, execute_energyplan_spool,
                        parse_output)
from moea.config import ENERGYPLAN_RESULTS


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

    def __init__(self,
                 data_file: str | Path = 'CEISCompleteCurrent.txt',
                 **kwargs):
        """
        The problem class replicates the model in:

        > Mahbub, Md Shahriar, Diego Viesi, and Luigi Crema (2016).
        > Designing optimized energy scenarios for an Italian Alpine valley:
        > the case of Giudicarie Esteriori. *Energy* 116, 236-249.

        """
        
        vars = {
            "input_RES1_capacity": Real(bounds=(5000, 42000)),  # PV capacity
            "input_fuel_Households[2]": Real(bounds=(0, 1)),  # Oil boiler heat %
            "input_fuel_Households[3]": Real(bounds=(0, 1)),  # Ngas boiler heat %
            "input_fuel_Households[4]": Real(bounds=(0, 1)),  # Biomass boiler heat %
            "input_HH_BioCHP_heat": Real(bounds=(0, 1)),  # Biomass micro-CHP heat %
            "input_HH_HP_heat": Real(bounds=(0, 1)),  # Individual HP %
        }

        super().__init__(vars=vars, n_obj=4, data_file=data_file, **kwargs)

    def _evaluate(self, x, out, *args, **kwargs):
        # Use enums for the percentage variables
        PV = 0
        OIL = 1
        LPG = 2
        BIOMASS = 3
        CHP = 4
        HP = 5

        for i, ind in enumerate(x):
            # Collect the variables
            z = np.array(list(ind.values()))
            # Sort percentages
            z[OIL:] = np.sort(z[OIL:])
            # Calculate percentages
            z[LPG] = z[LPG] - z[OIL]
            z[BIOMASS] = z[BIOMASS] - z[LPG]
            z[CHP] = z[CHP] - z[BIOMASS]
            z[HP] = 1 - z[CHP]

            # Compute variables
            z[OIL] = z[OIL] * self.totalHeatDemand / self.oilBoilerEfficiency
            z[LPG] = z[LPG] * self.totalHeatDemand / self.ngasBoilerEfficiency
            z[BIOMASS] = z[BIOMASS] * self.totalHeatDemand / \
                self.biomassBoilerEfficiency
            z[CHP] = z[CHP] * self.totalHeatDemand
            z[HP] = z[HP] * self.totalHeatDemand

            # Set variable values
            ind[OIL] = z[OIL]
            ind[LPG] = z[LPG]
            ind[BIOMASS] = z[BIOMASS]
            ind[CHP] = z[CHP]
            ind[HP] = z[HP]

        # Dump the input vectors to files
        for i, ind in enumerate(x):
            dump_input(ind, i)

        # Compute the objective functions
        execute_energyplan_spool([f"input{i}.txt" for i in range(len(x))])

        # Retrieve CO2 emissions and total annual costs
        co2, total_cost, variable_cost, operations_cost = find_values(
            ENERGYPLAN_RESULTS,
            "CO2-emission (corrected)",
            "TOTAL ANNUAL COSTS",
            "Variable costs",
            "Fixed operation costs"
        ).T

        # Retrieve:
        # - annual hydropower
        # - annual PV electricity
        # - annual wave power
        # - annual import
        # - annual export
        # - annual HH electricity CHP

        annual_lbl = 'TOTAL FOR ONE YEAR (TWh/year)'
        montly_lbl = 'MONTHLY AVERAGE VALUES (MW)'
        hydro, pv, wave, import_, export_, hh_chp = [], [], [], [], [], []
        for res in ENERGYPLAN_RESULTS.glob("*.txt"):
            D = parse_output(res)
            hydro.append(float(D[annual_lbl]["Hydro Electr."]))
            pv.append(float(D[annual_lbl]["PV Electr."]))
            wave.append(float(D[float]["Wave Electr."]))
            import_.append(float(D[float]["Import Electr."]))
            export_.append(float(D[float]["Export Electr."]))
            hh_chp.append(float(D[float]["HH-CHP Electr."]))
