import numpy as np
import os
import pandas as pd
from typing import Union
from pathlib import Path
from moea.utils import dump_input, find_values, execute_energyplan_spool
from moea.config import ENERGYPLAN_RESULTS
from moea.models.base_model import BaseModel


class RivadelGarda(BaseModel):
    """
    This model explores the possible decarbonisation
    scenarios for the existing District Heating Network (DHN) in Riva del Garda, Italy,
    with two objectives: total annual cost and total CO2 emissions.

    The reference input file is ``Riva_future1.txt``
    """

    def __init__(self,
                 data_file: Union[str, Path] = "Riva_future1.txt",
                 **kwargs):
        """
        Parameters:
        -----------
        - ``data_file``: str or Path

            The path to the input file. This file is used as a template to
            generate the input files for each individual.
            The values will be replaced by the values of the decision variables
            when generating the input files.
        """

        self.vars = pd.DataFrame.from_dict({
            'input_Waste2_Waste': {"lb": 0, "ub": 86.678},
            'input_cshp_th_gr2': {"lb": 0, "ub": 59.507},
            'input_cap_chp2_el': {"lb": 0, "ub": 3632},
            'input_eff_hp2_cop': {"lb": 1, "ub": 2.4},
            'input_cap_hp2_el': {"lb": 7630, "ub": 18312.5},
            'input_solar_storage_gr2': {"lb": 0, "ub": 20000},
            'input_solar_ann_gr2': {"lb": 0, "ub": 321},
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

        self.generation = 0  # Add generation counter

        # Define CSV file path
        self.csv_file = "Riva_future1results.csv"

        # If CSV doesn't exist, initialize it with headers
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, "w") as f:
                headers = ["Generation", "Individual"] + \
                          [f"X{i}" for i in range(self.n_var)] + \
                          ["CO2_Emissions", "Total_Cost","El_Import",
                           "waste2_waste", "cshp_th_gr2", "cap_chp2_el",
                           "HP2_Heat", "solar_storage_gr2", "solar_ann_gr2",
                           "solar_loss_gr2", "Boiler2_Heat",
                           "Boiler2_Capacity", "Balance2_Heat"]
                f.write(",".join(headers) + "\n")


    def _evaluate(self, x, out, *args, **kwargs):

        # Iterate over individuals and create an input file for each one
        # Dump the input vector to a file

        # --------------
        def preprocess_variables(variables, decimal_places=3, threshold=1e-3):
            """
            Preprocesses decision variables before passing to EnergyPLAN.
            - Sets very small values to zero if below the threshold.
            - Rounds other values while keeping them within their bounds.

            Args:
                variables (dict): Dictionary of decision variables.
                decimal_places (int): Decimal places to round to.
                threshold (float): Values below this are set to zero.

            Returns:
                dict: Processed decision variables.
            """
            processed_vars = {}

            for key, value in variables.items():
                # If value is smaller than threshold, set to zero
                if abs(value) < threshold:
                    processed_vars[key] = 0
                else:
                    processed_vars[key] = round(value, decimal_places)  # Keep precision

           # Conditional logic for input_solar_loss_gr2 and input_Inv_Heatstorage3
            solar_storage = processed_vars.get('input_solar_storage_gr2', 0)
            if 0 <= solar_storage <= 15:
                processed_vars['input_solar_loss_gr2'] = 0.1
                processed_vars['input_Inv_Heatstorage3'] = 20
            elif 15 < solar_storage <= 105:
                processed_vars['input_solar_loss_gr2'] = 0.2
                processed_vars['input_Inv_Heatstorage3'] = 10
            elif 105 < solar_storage <= 420:
                processed_vars['input_solar_loss_gr2'] = 0.3
                processed_vars['input_Inv_Heatstorage3'] = 1
            elif 420 < solar_storage <= 20000:
                processed_vars['input_solar_loss_gr2'] = 0.4
                processed_vars['input_Inv_Heatstorage3'] = 0.2
            else:
                processed_vars['input_solar_loss_gr2'] = 0  # Default value if out of range
                processed_vars['input_Inv_Heatstorage3'] = 0  # Default value if out of range

            return processed_vars

        # --------------
        # Start with default peak boiler capacity at beginning of every generation
        self.fixed_boiler_capacity = 18312.5

        for i, ind in enumerate(x):
            # Create a dictionary of decision variables
            decision_vars = {k: ind[j] for j, k in enumerate(self.vars.index)}
            # Preprocess values before writing them to the input file
            processed_vars = preprocess_variables(decision_vars)
            # Add the fixed boiler capacity into processed variables
            processed_vars["input_cap_boiler2_th"] = self.fixed_boiler_capacity
            # print("the first values",processed_vars)
            # Dump preprocessed values to EnergyPLAN input file
            dump_input(processed_vars, i, self.default_data)

        # Call EnergyPLAN using spool mode
        execute_energyplan_spool([f"input{i}.txt" for i in range(len(x))])

        # Retrieve values for boiler heat
        actual_boiler_capacity = find_values(
            ENERGYPLAN_RESULTS,
            ("Annual Maximum", "Boiler 2 Heat")
            ).ravel()

        # Dump the full list of variables to a file
        for i, ind in enumerate(x):
            # Create a dictionary of decision variables
            decision_vars = {k: ind[j] for j, k in enumerate(self.vars.index)}
            # Preprocess values before writing them to the input file
            processed_vars = preprocess_variables(decision_vars)
            # While keeping other variables as the as previous run, update boiler capacity
            processed_vars["input_cap_boiler2_th"] = actual_boiler_capacity[i]
            # print("the second values",processed_vars)
            # Dump preprocessed values to EnergyPLAN input file
            dump_input(processed_vars, i, self.default_data)

        # Call EnergyPLAN second time using spool mode
        execute_energyplan_spool([f"input{i}.txt" for i in range(len(x))])
        # Parse the output file
        Y = find_values(
            ENERGYPLAN_RESULTS,
            "CO2-emission (corrected)",
            "TOTAL ANNUAL COSTS",
            ("Annual", "Import Electr."),
            ("Annual", "waste2_waste"),
            ("Annual", "cshp_th_gr2"),
            ("Annual","cap_chp2_el"),
            ("Annual", "HP2_Heat"),
            ("Annual", "solar_storage_gr2"),
            ("Annual","solar_ann_gr2"),
            ("Annual","solar_loss_gr2"),
            ("Annual", "Boiler2 Heat"),
            ("Annual Maximum","Boiler2_Heat"),
            ("Annual","Boiler2_Capacity"),
            ("Annual", "Balance2_Heat"),
        )

        electricity_import = Y[:, 2]
        in_waste2_waste = Y[:, 3]
        cshp_th_gr2 = Y[:, 4]
        COP = x[:, 0]
        HP_EB_capacity = x[:, 1]
        HP_share = (COP-1)/(2.4-1)
        HP_el_capacity = HP_EB_capacity * HP_share
        EB_el_capacity = HP_EB_capacity - HP_el_capacity
        EB_th_capacity = EB_el_capacity * 1
        cost_HP = (HP_el_capacity * 485.6 * 0.04662)/(1-(1 + 0.04662)**-25) \
            + HP_el_capacity * 485.6 * 0.0248
        cost_EB = (EB_th_capacity * 112 * 0.04662)/(1-(1 + 0.04662)**-20) \
            + EB_th_capacity * 112 * 0.00446
        revenue_WtE = in_waste2_waste * 0.16 * 127 # GWh * Keuro/GWh
        # Industrial CHP heat cost and carbon emission
        cost_cshp_th_gr2 = cshp_th_gr2 * 12.5  # kEUR
        CO2_cshp_th_gr2 = cshp_th_gr2 * 0.242  # kton CO2
        cost_add = cost_HP + cost_EB + cost_cshp_th_gr2 - revenue_WtE
        CO2_el_import = electricity_import * (0.054*0.341 + 0.039*0.267 + 0.45*0.202) # ktCO2/GWh

        CO2_add = CO2_el_import + CO2_cshp_th_gr2
        # Update objective values
        out["F"] = np.column_stack([Y[:, 0] + CO2_add, Y[:, 1] + cost_add])
        # Save results to CSV
        df = pd.DataFrame({
            "Generation": self.generation,
            "Individual": np.arange(len(out["F"])),
        })
        for i in range(x.shape[1]):
            df[f"X{i}"] = x[:, i]
        df["CO2_Emissions"] = out["F"][:, 0]
        df["Total_Cost"] = out["F"][:, 1]
        df["El_Import"] = Y[:, 2]
        df["waste2_waste"] = Y[:,3]
        df["cshp_th_gr2"] = Y[:,4]
        df["cap_chp2_el"] = Y[:,5]
        df["HP2_Heat"] = Y[:, 6]
        df["solar_storage_gr2"] = Y[:,7]
        df["solar_ann_gr2"] = Y[:,8]
        df["solar_loss_gr2"] = Y[:, 9]
        df["Boiler2_Heat"] = Y[:, 10]
        df["Boiler2_Capacity"] = Y[:, 12]
        df["Balance2_Heat"] = Y[:, 13]

        # Append data to the CSV file
        df.to_csv(self.csv_file, mode="a", header=False, index=False)
        # Increment generation counter for next call
        self.generation += 1


if __name__ == "__main__":
    pass
