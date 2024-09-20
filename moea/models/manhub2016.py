from typing import Union
from pathlib import Path

from pymoo.core.variable import Real


from moea.utils import dump_input, find_values, execute_energyplan_spool
from moea.config import ENERGYPLAN_RESULTS
from moea.models.base_model import BaseModel


class Manhub2016(BaseModel):
    """
    This problem class replicates the model in

    > Mahbub, M. S., Cozzini, M., Østergaard, P. A., Alberti, F. (2016). Combining multi-objective evolutionary algorithms and descriptive analytical modelling in energy scenario design. Applied Energy, 164, 140-151.

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
        # Store the constraint violation in the output dictionary. This is not
        # used in this problem, but it is included for completeness.
        # out["G"] = 0