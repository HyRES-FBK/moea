import numpy as np
import pandas as pd
from typing import Union
from pathlib import Path

from pymoo.core.variable import Real


from moea.utils import (dump_input, find_values, execute_energyplan_spool,
                        parse_output)
from moea.config import ENERGYPLAN_RESULTS
from moea.models.base_model import BaseModel


class Manhub2016(BaseModel):
    """
    This problem class replicates the model in

    > Mahbub, M. S., Cozzini, M., Østergaard, P. A., Alberti, F. (2016).
    > Combining multi-objective evolutionary algorithms and descriptive
    > analytical modelling in energy scenario design. *Applied Energy*,
    > 164, 140-151.

    There are six decision variables, which are the capacities of power
    plants, CHP, heat pump, onshore wind, offshore wind, and PV, and one free
    variable, that is the capacity of group 3 boiler, which does not have an
    effect on the value of the objectives. The objectives are the total CO2
    emissions and the total annual costs.

    The reference input file is ``Aalborg2050_2objctives.txt``.
    """

    def __init__(self,
                 data_file: Union[str, Path] = "Aalborg2050_2objectives.txt",
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
        # Define the input variables.
        self.vars = pd.DataFrame.from_dict({
            'input_cap_chp3_el': {'lb':0, 'ub': 1000},
            'input_cap_hp3_el': {'lb':0, 'ub': 1000},
            'input_cap_pp_el': {'lb': 0, 'ub': 1000},
            'input_RES1_capacity': {'lb': 0, 'ub': 1500},
            'input_RES2_capacity': {'lb': 0, 'ub': 1500},
            'input_RES3_capacity': {'lb': 0, 'ub': 1500},
            'input_cap_boiler3_th': {'lb': 0, 'ub': 10000},
        }, dtype=float, orient='index')

        # Initialize the parent class
        super().__init__(
            n_var=len(self.vars),
            n_ieq_constr=3,
            n_obj=2,
            xl=self.vars['lb'].values,
            xu=self.vars['ub'].values,
            data_file=data_file,
            **kwargs
        )

    def _evaluate(self, x, out, *args, **kwargs):
        """
        This function defines the evaluation of the problem. That is, the
        objective function and constraints are evaluated here. The objective
        function evaluation consists of a call to EnergyPLAN. Since the problem
        is unconstrained, the constraints are not evaluated.

        """
        # Iterate over individuals and create an input file for each one
        # Dump the input vector to a file
        keys_to_exclude = ['input_cap_boiler3_th', 'input_cap_pp_el']
        for i, ind in enumerate(x):
            # Overwrite the values in self.data with the values in ind
            dump_input({k: ind[j] for j, k in enumerate(self.vars.index)
                        if k not in keys_to_exclude}, i, self.default_data)

        # Call EnergyPLAN using spool mode; only the input files are needed
        execute_energyplan_spool([f"input{i}.txt" for i in range(len(x))])

        # The label for the monthly values
        montly_lbl = 'MONTHLY AVERAGE VALUES (MW)'
        # For ease of reference, we define the indices of the variables
        PP = 2
        BOILER = 6
        # Retrieve values for boiler heat and PP capacity
        for i, res in enumerate(ENERGYPLAN_RESULTS.glob("*.txt")):
            D = parse_output(res)
            x[i, BOILER] = \
                np.float64(D[montly_lbl]['Boiler 3  Heat']['Annual Maximum'])
            x[i, PP] = \
                np.float64(D[montly_lbl]['PP Electr.']['Annual Maximum'])

        # Dump the full list of variables to a file
        for i, ind in enumerate(x):
            dump_input({k: ind[j] for j, k in enumerate(self.vars.index)}, i,
            self.default_data)

        # Call EnergyPLAN using spool mode; only the input files are needed
        execute_energyplan_spool([f"input{i}.txt" for i in range(len(x))])

        # Parse the output file and store the objective function value in an
        # array
        out["F"] = find_values(
            ENERGYPLAN_RESULTS,
            "CO2-emission (corrected)",
            "TOTAL ANNUAL COSTS",
        )

        # CONSTRAINTS
        # Since there are a fes constraints, we evaluate the left-hand side
        # of the constraints and store the values in out["G"].

        # Read and store the values of interest into arrays
        import_elec, heat, stable_load = [], [], []
        for res in ENERGYPLAN_RESULTS.glob("*.txt"):
            # Parse the output file
            D = parse_output(res)
            # Results are organized as dictionary, one for each section, and
            # each value is a pandas DataFrame
            # Retrieve import
            import_elec.append(
                float(D[montly_lbl]['Import Electr.']['Annual Maximum']))
            # Retrieve Balance3 heat
            heat.append(
                float(D['TOTAL FOR ONE YEAR (TWh/year)']['Balance3  Heat']))
            # Retrieve stabilized load percentage
            stable_load.append(
                float(D[montly_lbl]['Stabil. Load']['Annual Minimum']))

        # Transmission line capacity of export/import: 160 MW. This constraint
        # enforces the system to produce enough electricity so that it does not
        # require to import more than 160 MW.
        import_constr = np.array(import_elec) - 160

        # Heat balance. This constraint enforces the system to produce exactly
        # the amount of heat necessary to meet the heat demand.
        heat = np.array(heat)

        # Grid stabilization: More than 30% of power production in all hours
        # must come from units able to supply grid support (see [77] for
        # details on grid stability in EnergyPLAN).
        # This constraint is already taken into account by EnergyPLAN so we
        # just need to subtract the value from 100 to have a constraint that
        # is satisfied when the value is positive.
        stable_load = 100 - np.array(stable_load)

        out["G"] = np.column_stack([
            import_constr,
            stable_load,
            heat,
        ])


if __name__ == "__main__":
    pass
