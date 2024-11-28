from typing import Union
from pathlib import Path

from pymoo.core.problem import Problem

from moea.utils import parse_input
from moea.config import ENERGYPLAN_DATA_DIR


class BaseModel(Problem):
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

    def __init__(self,
                 data_file: Union[str, Path],
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
        # Check if data file exists
        if not data_file:
            raise ValueError("Data file must be provided.")
        # If data file is string convert to Path
        if type(data_file) is str:
            data_file = Path(data_file)
        # Add .txt extension if it is missing
        if data_file.suffix == "":
            data_file = data_file.with_suffix(".txt")
        # Check that the data file name ends with .txt
        if data_file.suffix != ".txt":
            raise ValueError("Data file must be a text file.")
        # Provide full path for the data file
        data_file = ENERGYPLAN_DATA_DIR / data_file
        # Check that the data file exists
        if not data_file.exists():
            raise FileNotFoundError(f"Data file {data_file} not found.")
        # Read data file and store values
        self.default_data = parse_input(data_file)

        # Initialize the parent class
        super().__init__(**kwargs)


    def _evaluate(self, x, out, *args, **kwargs):
        """
        This function defines the evaluation of the problem. That is, the
        objective function and constraints are evaluated here. The objective
        function evaluation consists of a call to EnergyPLAN. Since the problem
        is unconstrained, the constraints are not evaluated.

        """
        return super()._evaluate(x, out, *args, **kwargs)


if __name__ == "__main__":
    pass
