from pathlib import Path

from pymoo.core.problem import Problem


class BaseModel(Problem):
    """
    Declaration of the optimization problem. The input variables are
    defined here, as well as the number of objectives and constraints.
    EnergyPLAN allows the user to define more than a thousand variables,
    depending on the model being used. The lower and upper bounds of variables
    must be passed using arguments `xl` and `xu`.
    """

    def __init__(self,
                 data_file: str | Path,
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
        if data_file is None:
            raise ValueError("Data file must be provided.")
        if type(data_file) is str:
            data_file = Path(data_file)
        # Read data file and store values
        self.energyplan = getattr(self, "energyplan_version")(
            energyplan_data_file=data_file
        )

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
