import numpy as np
import pandas as pd
from typing import Union
from pathlib import Path

from moea.utils import dump_input, find_values, execute_energyplan_spool
from moea.config import ENERGYPLAN_RESULTS
from moea.models.base_model import BaseModel


class Aalborg(BaseModel):
    """
    This problem class replicates the model in

    > Mahbub, M. S., Cozzini, M., Østergaard, P. A., Alberti, F. (2016).
    > Combining multi-objective evolutionary algorithms and descriptive
    > analytical modelling in energy scenario design. *Applied Energy*,
    > 164, 140-151.

    There are seven decision variables, which are the capacities of power
    plants, CHP, heat pump, onshore wind, offshore wind, PV, and one free
    variable, that is the capacity of group 3 boiler, which does not have an
    effect on the value of the objectives. The objectives are the total CO2
    emissions and the total annual costs.

    In this version of the Aalborg model, EnergyPLAN is called twice. The first
    call is used to evaluate the objective functions without the boiler
    capacity and the PP capacity. The second call is used to evaluate the
    constraints. The boiler capacity and the PP capacity are evaluated in the
    first call and then used in the second call.

    The reference input file is
    ``Aalborg_2050_Plan_A_44ForOptimization_2objectives.txt``.
    """

    # Large value for boiler & PP and other information
    largeValueOfBoiler = 1500
    largeValueOfPP = 1000
    boilerLifeTime = 20
    PPLifeTime = 30
    interest = 0.03
    fixedMOForBoilerinPercentage = 0.03
    fixedMOForPPinPercentage = 0.02
    boilerCostInMDDK = 1.0
    PPCostInMDKK = 0.0

    def __init__(self,
                 data_file: Union[str, Path] = \
                    "Aalborg_2050_Plan_A_44ForOptimization_2objectives.txt",
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
            'input_cap_chp3_el': \
                {'lb':0, 'ub': 1000, "dk0": True, "dk1": False},
            'input_cap_hp3_el': \
                {'lb':0, 'ub': 1000, "dk0": True, "dk1": False},
            'input_cap_pp_el': \
                {'lb': 0, 'ub': 1000, "dk0": None, "dk1": None},
            'input_RES1_capacity': \
                {'lb': 0, 'ub': 1500, "dk0": True, "dk1": False},
            'input_RES2_capacity': \
                {'lb': 0, 'ub': 1500, "dk0": True, "dk1": False},
            'input_RES3_capacity': \
                {'lb': 0, 'ub': 1500, "dk0": True, "dk1": False},
            'input_cap_boiler3_th': \
                {'lb': 0, 'ub': 250, "dk0": None, "dk1": None},
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
        # Dump the full list of variables to a file
        for i, ind in enumerate(x):
            dump_input({k: ind[j] for j, k in enumerate(self.vars.index)},
                        i, self.default_data)

        # Call EnergyPLAN using spool mode; only the input files are needed
        execute_energyplan_spool([f"input{i}.txt" for i in range(len(x))])

        # Parse the output file
        Y = find_values(
            ENERGYPLAN_RESULTS,
            "CO2-emission (corrected)",
            "TOTAL ANNUAL COSTS",
            ("Annual Maximum", "Import Electr."),
            ("Annual", "Balance3 Heat"),
            ("Annual Minimum", "Stabil. Load"),
        )

        # The CO2 emissions are set directly from the results files, whereas
        # the cost is adjusted by the reduction in investment and fixed O&M
        # for the cases where CHP > PP.
        out["F"] = Y[:, :2]

        # CONSTRAINTS
        # Since there are a fes constraints, we evaluate the left-hand side
        # of the constraints and store the values in out["G"].

        # Transmission line capacity of export/import: 160 MW. This constraint
        # enforces the system to produce enough electricity so that it does not
        # require to import more than 160 MW.
        import_constr = np.array(Y[:, 2]) - 160

        # Heat balance. This constraint enforces the system to produce exactly
        # the amount of heat necessary to meet the heat demand.
        heat = - np.array(Y[:, 3])

        # Grid stabilization: More than 30% of power production in all hours
        # must come from units able to supply grid support (see [77] for
        # details on grid stability in EnergyPLAN).
        # This constraint is already taken into account by EnergyPLAN so we
        # just need to subtract the value from 100 to have a constraint that
        # is satisfied when the value is positive.
        stable_load = 100 - np.array(Y[:, 4])

        out["G"] = np.column_stack([
            import_constr,
            stable_load,
            heat,
        ])


if __name__ == "__main__":
    pass
