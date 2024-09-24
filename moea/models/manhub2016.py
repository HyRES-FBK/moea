import numpy as np
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
    plants, CHP, heat pump, onshore wind, offshore wind, and PV. The
    objectives are the total CO2 emissions and the total annual costs.

    The reference input file is `Manhub2016.txt`, which is a modified
    version of the input file ``Denmark2030Reference.txt``.
    """

    def __init__(self,
                 data_file: Union[str, Path] = "Aalborg2050_vision.txt",
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
        # Define the input variables. The variables chosen here are the same
        # as the ones used in EPLANopt https://github.com/matpri/EPLANopt.git
        vars = {
            'input_cap_chp3_el': Real(bounds=(0, 1000)),  # CHP capacity
            'input_cap_hp3_el': Real(bounds=(0, 1000)),  # HP capacity
            'input_cap_pp_el': Real(bounds=(0, 1000)),  # PP capacity
            'input_RES1_capacity': Real(bounds=(0, 1500)),  # Onshore wind
            'input_RES2_capacity': Real(bounds=(0, 1500)),  # Offshore wind
            'input_RES3_capacity': Real(bounds=(0, 1500)),  # PV capacity
        }

        objectives = [
            "CO2-emission (total)",
            "TOTAL ANNUAL COSTS",
        ]

        # Initialize the parent class
        super().__init__(
            vars=vars,
            objectives=objectives,
            data_file=data_file,
            **kwargs
        )

    def _evaluate(self, x, out, *args, **kwargs):
        """
        This function defines the evaluation of the problem. That is, the
        objective function and constraints are evaluated here. The objective
        function evaluation consists of a call to EnergyPLAN. Since the problem
        is unconstrained, the constraints are not evaluated.

        When defining a new problem, the user should NOT modify this function
        but should modify only the ``__init__`` function to define variables
        and objectives. The only exception is if the user wants to define a
        new problem with constraints, in which case the constraints should be
        evaluated in this function and stored in ``out[G]``.
        """
        # Iterate over individuals and create an input file for each one
        # Dump the input vector to a file
        for i, ind in enumerate(x):
            dump_input(ind, i)

        # Call EnergyPLAN using spool mode; only the input files are needed
        execute_energyplan_spool([f"input{i}.txt" for i in range(len(x))])

        # Parse the output file and store the objective function value in an
        # array
        out["F"] = find_values(
            ENERGYPLAN_RESULTS,
            *self.objectives
        )

        # CONSTRAINTS
        # Since there are a fes constraints, we evaluate the left-hand side
        # of the constraints and store the values in out["G"].

        # Read and store the values of interest into arrays
        import_elec = []
        heat_prod, heat_demand = [], []
        stable_load = []
        for out in ENERGYPLAN_RESULTS.glob(".txt"):
            # Parse the output file
            D = parse_output(out)
            # Results are organized as dictionary, one for each section, and
            # each value is a pandas DataFrame
            montly_lbl = 'MONTHLY AVERAGE VALUES (MW)'
            # Retrieve import
            import_elec.append(
                D[montly_lbl]['Import Electr.']['Annual Maximum'] \
                    .astype(float))
            # Retrieve Balance3 heat
            heat_prod.append(
                D['TOTAL FOR ONE YEAR (TWh/year)']['Balance3  heat'] \
                    .astype(float))
            # Retrieve heat demand
            heat_demand.append(
                D[montly_lbl]['DH Demand'].astype(float).sum())
            # Retrieve stabilized load percentage
            stable_load.append(
                D[montly_lbl]['Stabil. Load']['Annual Minimum'].astype(float))

        # Transmission line capacity of export/import: 160 MW. This constraint
        # enforces the system to produce enough electricity so that it does not
        # require to import more than 160 MW.
        import_constr = np.array(import_elec) - 160

        # Heat balance. This constraint enforces the system to produce exactly
        # the amount of heat necessary to meet the heat demand.
        heat = np.array(heat_demand) - np.array(heat_prod)

        # Grid stabilization: More than 30% of power production in all hours
        # must come from units able to supply grid support (see [77] for
        # details on grid stability in EnergyPLAN).
        # This constraint is already taken into account by EnergyPLAN
        stable_load = 0.3 - np.array(stable_load) / 100

        out["G"] = np.concatenate([
            import_constr,
            stable_load,
        ])

        out["H"] = np.array([
            heat,
        ])
