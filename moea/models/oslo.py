import numpy as np
import pandas as pd
from typing import Union
from pathlib import Path

from moea.utils import dump_input, find_values, execute_energyplan_spool
from moea.config import ENERGYPLAN_RESULTS
from moea.models.base_model import BaseModel


class AalborgA(BaseModel):
    """
    Description of the model
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

        self.vars = pd.DataFrame.from_dict({
            'input_RES1_capacity': {"lb": 0, "ub": 1},
        })

        # Initialize the parent class
        super().__init__(
            n_var=len(self.vars),
            n_ieq_constr=1,
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
        # Dump the full list of variables to a file, this can be used if
        # variable names correspond to the names in the input file
        for i, ind in enumerate(x):
            dump_input({k: ind[j] for j, k in enumerate(self.vars.index)}, i,
            self.default_data)

        # Call EnergyPLAN using spool mode; only the input files are needed
        execute_energyplan_spool([f"input{i}.txt" for i in range(len(x))])

        # Parse the output file and store the objective function value in an
        # array
        X = find_values(
            ENERGYPLAN_RESULTS,
            "CO2-emission (corrected)",
            "TOTAL ANNUAL COSTS",
            ("Annual Maximum", "Import Electr."),
            ("Annual", "Balance3 Heat"),
            ("Annual Minimum", "Stabil. Load"),
        )

        # The objective function values are stored in the first two columns
        out["F"] = X[:, :2]

        # CONSTRAINTS
        out["G"] = np.zeros((x.shape[0], 1))


if __name__ == "__main__":
    pass
