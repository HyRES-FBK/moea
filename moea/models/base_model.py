from typing import Union
from pathlib import Path

from pymoo.core.problem import Problem
from pymoo.core.variable import Real


from moea.utils import dump_input, find_values, execute_energyplan_spool
from moea.config import ENERGYPLAN_RESULTS


class BaseProblem(Problem):
    """
    Declaration of the optimization problem. The input variables are
    defined here, as well as the number of objectives and constraints.
    EnergyPLAN allows the user to define more than a thousand variables,
    depending on the model being used. The file
    ``EnergyPLAN/spool/input.json`` is the template used to generate the
    input files for the optimization. Only the variables that are being
    declared here are modified in the input files.
    The lower and upper bounds of the variables are also defined here.
    The base problem is defined as a single objective problem with no
    constraints.
    """

    def __init__(self, data_file: Union[str, Path], **kwargs):
        """
        Parameters:
        -----------
        - ``data_file``: str or Path

            The path to the input file. This file is used as a template to
            generate the input files for each individual.
            The values will be replaced by the values of the decision variables
            when generating the input files.
        """
        # If data file is string convert to Path
        if type(data_file) is str:
            data_file = Path(data_file)
        # Add .txt extension if it is missing
        if data_file.suffix == "":
            data_file = data_file.with_suffix(".txt")
        # Check that the data file name ends with .txt
        if data_file.suffix != ".txt":
            raise ValueError("Data file must be a text file.")
        self.data_file = data_file

        # Define the input variables. The variables chosen here are the same
        # as the ones used in EPLANopt https://github.com/matpri/EPLANopt.git
        vars = {
            'input_RES1_capacity':      Real(bounds=(17, 100)),
            'input_cap_pp_el':          Real(bounds=(0, 1)),
            'input_storage_pump_cap':   Real(bounds=(0, 75)),
        }

        self.objectives = [
            "TOTAL ANNUAL COSTS",
            "CO2-emission (total)"
        ]

        # Initialize the parent class
        super().__init__(
            vars=vars,
            n_obj=len(self.objectives),     # The problem has one objective
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
            dump_input(ind, i, self.data_file)

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