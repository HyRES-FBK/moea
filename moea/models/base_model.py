from typing import Union, Dict
from pathlib import Path

from pymoo.core.problem import Problem
from pymoo.core.variable import Real


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
                 vars: Dict[str, Real],
                 data_file: Union[str, Path],
                 **kwargs):
        """
        Parameters:
        -----------
        - ``vars``: dict

            A dictionary containing variable names as keys and PyMOO type
            objects as variables.

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

        # Initialize the parent class
        super().__init__(
            vars=vars,
            **kwargs
        )

    
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
