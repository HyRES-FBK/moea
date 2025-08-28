import os
import numpy as np
import pandas as pd
from typing import Union
from pathlib import Path

from moea.models.base_model import BaseModel
from moea.energyplan.energyplan163 import EnergyPLAN163


class Oslo(BaseModel):
    """
    The reference input file is ``Oslo_2objectives_baseline.txt``, which must
    be stored in \moea\EnergyPLAN\energyPlan Data\Data. This reference input
    text file is used to define all variables needed by the proper execution of
    EnergyPLAN baseline scenario for Oslo DHN. To explore the decarbonization
    scenarios, some of these variables are taken as decision variables and
    their values are modified (initially randomly) within the lower bound and
    upper bound.
    """

    energyplan_version = EnergyPLAN163

    def __init__(self,
                 data_file: Union[str, Path] = "Oslo_2objectives_baseline.txt",
                 **kwargs):
        """
        Parameters:
        -----------
        - ``data_file``: str or Path
            The path to the input file. This file is used as a template to
            generate the input files for each individual. The values will be
            replaced by the values of the decision variables when generating
            the input files.
        """
        # Definition of decision variables, with their power and upper bounds
        """
        The mentioned decision variables in problem definition section are listed
        here. To modify these decision variables on EnergyPLAN, their unique naming
        on the software input text file are found. For example, to modify the
        waste-to-energy plant fuel input value under the group 2, the correct
        variable name used in EnergyPLAN is "input_Waste2_Waste".

        The definition of the district heating boiler capacity under supply section
        of EnergyPLAN is done by the following variable: "input_cap_boiler2_th".
        To define the fuel shares (among natural gas, oil and biomass) of this
        total capacity, the following variables are used, respectively:

        ```
        input_fuel_Boiler2[2]
        input_fuel_Boiler2[3]
        input_fuel_Boiler2[4]
        ```

        Since the boiler is a peak supply technology, the total capacity of the
        boiler is not defined as a decision variable here. To be sure that this
        peak demand is satisfied by the boilers, the random values are assigned
        for other technologies first, with a high boiler capacity, and the software
        is executed. Then, the results are obtained for all individuals and the
        boiler maximum power is read and replaced with the high capacity defined
        in the beginning. This approach guarantees the satisfaction of the demand
        considering the need boiler cpacity only.

        The lower and upper bound values are calculated considering some physical
        constarints of the case study.

        The last clarification of the decision variable list is about heat pump
        and electric boiler definitions in this optimization. The EnergyPLAN kicks
        the electric boiler in the production when there is excess of electricity
        in the system. Since there is no electricity modelling in this case study,
        i.e. district heating only modelling, the electric boiler usage is done by
        defining the heat pump COP value as 1. For the heat pump utulization, the
        COP value is defined as 3.39. Therefore, COP value of heat pump 2 definition
        is taken here as a decision variable with its electric capacity. The cost
        of these two technologies are defined in the baseline file as zero, but the
        post-processing is done for the total annual cost correction before proceeding
        with the next generation.

        """
        self.vars = pd.DataFrame.from_dict({
            'input_Waste2_Waste': {"lb": 1.361, "ub": 2.722},
            'input_ind_surplus_heat2': {"lb": 0, "ub": 0.379},
            'input_fuel_Boiler2[2]': {"lb": 0, "ub": 1},
            'input_fuel_Boiler2[3]': {"lb": 0, "ub": 1},
            'input_fuel_Boiler2[4]': {"lb": 0, "ub": 1},
            'input_eff_hp2_cop': {"lb": 1, "ub": 3.39},
            'input_cap_hp2_el': {"lb": 0, "ub": 681},
            'input_storage_gr2_cap': {"lb": 0, "ub": 100},
            'input_CO2_CCS': {"lb": 0, "ub": 0.278},
        }, dtype=float, orient='index')

        # Initialize the parent class
        super().__init__(
            n_var=len(self.vars),
            n_ieq_constr=0,
            n_obj=2,
            xl=self.vars['lb'].values,
            xu=self.vars['ub'].values,
            data_file=data_file,
            **kwargs
        )
        # This part is added to store the decision variable values and
        # needed outputs of each individual in each generation in a cvs file.

        self.generation = 0  # Add generation counter

        # Define CSV file path
        self.csv_file = "oslo_results.csv"

        # If CSV doesn't exist, initialize it with headers
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, "w") as f:
                headers = ["Generation", "Individual"] + \
                          [f"X{i}" for i in range(self.n_var)] + \
                          ["CO2_Emissions", "Total_Cost","El_Import",
                           "Boiler2_Heat","HP2_Heat","Storage2_Heat",
                           "Balance2_Heat", "Boiler_Capacity"]
                f.write(",".join(headers) + "\n")


    @staticmethod
    def preprocess_variables(variables, decimal_places=3, threshold=1e-3):
        """
        Preprocesses decision variables before passing to EnergyPLAN.
        - Sets very small values to zero if below the threshold.
        - Rounds other values while keeping them within their bounds.

        Parameters:
        -----------
        - ``variables``: dict
            Dictionary of decision variables.
        - ``decimal_places``: int
            Decimal places to round to.
        - ``threshold``: float
            Values below this are set to zero.

        Returns:
        --------
        - ``preprocessed_vars``: dict
            Processed decision variables.
        """
        processed_vars = {}

        for key, value in variables.items():
            # If value is smaller than threshold, set to zero
            if abs(value) < threshold:
                processed_vars[key] = 0
            else:
                processed_vars[key] = round(value, decimal_places)  # Keep precision

        return processed_vars

    def _evaluate(self, x, out, *args, **kwargs):

        # Start with default peak boiler capacity at beginning of every generation
        self.fixed_boiler_capacity = 681

        decision_vars = [
            {k: ind[j] for j, k in enumerate(self.vars.index)} for ind in x
        ]

        processed_vars = [self.preprocess_variables(i) for i in decision_vars]

        # Add the fixed boiler capacity into processed variables
        for vars in processed_vars:
            vars["input_cap_boiler2_th"] = self.fixed_boiler_capacity

        # Call EnergyPLAN using spool mode
        self.energyplan.run(inputs=processed_vars)

        # Retrieve values for boiler heat
        actual_boiler_capacity = self.energyplan.read_values(
            ("Annual Maximum", "Boiler 2 Heat")
        ).ravel()

        # Add the fixed boiler capacity into processed variables
        for i, vars in enumerate(processed_vars):
            vars["input_cap_boiler2_th"] = actual_boiler_capacity[i]

        # Parse the output file
        Y = self.energyplan.read_values(
            "CO2-emission (corrected)",
            "TOTAL ANNUAL COSTS",
            "Oil Consumption",
            "Ngas Consumption",
            ("Annual", "Import Electr."),
            ("Annual", "Boiler 2 Heat"),
            ("Annual", "HP 2 Heat"),
            ("Annual", "Storage2 Heat"),
            ("Annual", "Balance2 Heat"),
            ("Annual Maximum", "Boiler 2 Heat"),
        )

        """
        After executing the EnergyPLAN twice, the first with a high boiler
        capacity, the second with the needed boiler capacity, some output data
        are collected and stored. These outputs can be read depending on the
        case study and post processing need. The post-processing of total CO2
        emission and the total annual cost are done for the following
        corrections in this case study:
        For the total annual cost:
            1. Annual cost of heat pump
            2. Annual cost of electric boiler
            3. Annual cost of CCS unit
            4. Cost of industrial excess heat
            5. Carbon pricing (fossil carbon emission price is different than
            waste burning carbon emission price)
            6. Revenue of electricty production by waste-to-energy plant
        For the total CO2 emissions:
            1. Electricty import (additional emissions according to national
            grid emission factor)
        """
        oil_consumption = Y[:, 2]
        ng_consumption = Y[:, 3]
        electricity_import = Y[:, 4]
        waste_input = x[:, 0]
        industrial_excess_heat = x[:, 1]
        COP = x[:, 5]
        HP_EB_capacity = x[:, 6]
        CCS_capacity = x[:, 8]

        HP_share = (COP - 1) / (3.39 - 1)
        HP_el_capacity = HP_EB_capacity * HP_share
        EB_el_capacity = HP_EB_capacity - HP_el_capacity
        EB_th_capacity = EB_el_capacity * 0.99

        cost_HP = (HP_el_capacity * 2.328 * 0.036) / (1 - (1 + 0.036)**-25) \
            + HP_el_capacity * 2.328 * 0.0031
        cost_EB = (EB_th_capacity * 0.138 * 0.036) / (1 - (1 + 0.036)**-20) \
            + EB_th_capacity * 0.138 * 0.0036
        cost_CCS = (CCS_capacity * 2077 * 0.036) / (1 - (1 + 0.036)**-25) \
            + CCS_capacity * 2077 * 0.03614
        cost_co2 = (
            oil_consumption * 74000 * 3.6 / 10**6 + \
                ng_consumption * 56700 * 3.6 / 10**6) * 77 + \
                    waste_input * 56890 * 3.6 / 10**6 * 20.84
        cost_industrial_excess_heat = industrial_excess_heat * 29
        revenue_WtE = waste_input * 0.1117 * 67

        cost_add = cost_HP + cost_EB + cost_CCS + cost_co2 + \
            cost_industrial_excess_heat - revenue_WtE

        co2_el_import = electricity_import * 0.0106

        co2_add = co2_el_import

        # Update objective values
        out["F"] = np.column_stack([Y[:, 0] + co2_add, Y[:, 1] + cost_add])


        # Save results to CSV
        df = pd.DataFrame({
            "Generation": self.generation,
            "Individual": np.arange(len(out["F"])),
        })

        for i in range(x.shape[1]):
            df[f"X{i}"] = x[:, i]

        df["CO2_Emissions"] = out["F"][:, 0]
        df["Total_Cost"] = out["F"][:, 1]
        df["El_Import"] = Y[:, 4]
        df["Boiler2_Heat"] = Y[:, 5]
        df["HP2_Heat"] = Y[:, 6]
        df["Storage2_Heat"] = Y[:, 7]
        df["Balance2_Heat"] = Y[:, 8]
        df["Boiler_Capacity"] = Y[:, 9]

        # Append data to the CSV file
        df.to_csv(self.csv_file, mode="a", header=False, index=False)

        # Increment generation counter for next call
        self.generation += 1


if __name__ == "__main__":
    pass
