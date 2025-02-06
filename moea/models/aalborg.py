import numpy as np
import pandas as pd
from typing import Union
from pathlib import Path

from moea.utils import dump_input, find_values, execute_energyplan_spool
from moea.config import ENERGYPLAN_RESULTS
from moea.models.base_model import BaseModel


class AalborgA(BaseModel):
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
                {'lb': 0, 'ub': 10000, "dk0": None, "dk1": None},
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
        # Dump the full list of variables to a file
        for i, ind in enumerate(x):
            dump_input({k: ind[j] for j, k in enumerate(self.vars.index)}, i,
            self.default_data)

        # Call EnergyPLAN using spool mode; only the input files are needed
        execute_energyplan_spool([f"input{i}.txt" for i in range(len(x))])

        # Parse the output file and store the objective function value in an
        # array
        Y = find_values(
            ENERGYPLAN_RESULTS,
            "CO2-emission (corrected)",
            "TOTAL ANNUAL COSTS",
            ("Annual Maximum", "Import Electr."),
            ("Annual", "Balance3 Heat"),
            ("Annual Minimum", "Stabil. Load"),
        )

        # The objective function values are stored in the first two columns
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
        heat = np.array(Y[:, 3])

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


class AalborgB(BaseModel):
    """
    In this version of the Aalborg model, EnergyPLAN is called twice. The first
    call is used to evaluate the objective functions without the boiler
    capacity and the PP capacity. The second call is used to evaluate the
    constraints. The boiler capacity and the PP capacity are evaluated in the
    first call and then used in the second call.
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
                {'lb': 0, 'ub': 10000, "dk0": None, "dk1": None},
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
        # Iterate over individuals and create an input file for each one
        # Dump the input vector to a file
        keys_to_exclude = ['input_cap_boiler3_th', 'input_cap_pp_el']
        for i, ind in enumerate(x):
            # Overwrite the values in self.data with the values in ind
            dump_input({k: ind[j] for j, k in enumerate(self.vars.index)
                        if k not in keys_to_exclude}, i, self.default_data)

        # Call EnergyPLAN using spool mode; only the input files are needed
        execute_energyplan_spool([f"input{i}.txt" for i in range(len(x))])

        # Retrieve values for boiler heat and PP capacity
        x[:, (2, 6)] = find_values(
            ENERGYPLAN_RESULTS,
            ("Annual Maximum", "PP Electr."),
            ("Annual Maximum", "Boiler 3 Heat"),
        )
        # Dump the full list of variables to a file
        for i, ind in enumerate(x):
            dump_input({k: ind[j] for j, k in enumerate(self.vars.index)}, i,
            self.default_data)

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

        # Append objectives to the output dictionary
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
        heat = np.array(Y[:, 3])

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


class AalborgC(BaseModel):
    """
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
                {'lb': 0, 'ub': 10000, "dk0": None, "dk1": None},
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
        # Iterate over individuals and create an input file for each one
        # Dump the input vector to a file
        keys_to_exclude = ['input_cap_boiler3_th', 'input_cap_pp_el']
        for i, ind in enumerate(x):
            # Overwrite the values in self.data with the values in ind
            dump_input({k: ind[j] for j, k in enumerate(self.vars.index)
                        if k not in keys_to_exclude}, i, self.default_data)

        # Call EnergyPLAN using spool mode; only the input files are needed
        execute_energyplan_spool([f"input{i}.txt" for i in range(len(x))])

        # Retrieve values for boiler heat and PP capacity
        maxPP, maxBoiler3 = find_values(
            ENERGYPLAN_RESULTS,
            ("Annual Maximum", "PP Electr."),
            ("Annual Maximum", "Boiler 3 Heat"),
        ).T

        # Find the individuals that need a second evaluation, CHP > PP
        mask = x[:, 0] > maxPP

        # Where CHP > PP, set the decision variables according to the maximum
        # power plant capacity and the maximum boiler capacity. The index 0
        # corresponds to the power plant capacity, and the index 2 corresponds
        # to the boiler capacity.
        x[:, 0] = np.where(mask, maxPP, x[:, 0])
        x[:, 2] = np.where(mask, maxPP, x[:, 2])

        # Set the decision variables according to the maximum boiler capacity
        x[:, 6] = np.where(mask, maxBoiler3, x[:, 6])

        # Dump the full list of variables to a file
        for i, ind in enumerate(x):
            if mask[i]:
                dump_input({k: ind[j] for j, k in enumerate(self.vars.index)},
                           i, self.default_data, clean_folder=False)

        # Call EnergyPLAN using spool mode; only the input files are needed
        execute_energyplan_spool([f"input{i}.txt" for i in range(len(x))
                                  if mask[i]])

        # Parse the output file
        Y = find_values(
            ENERGYPLAN_RESULTS,
            "CO2-emission (corrected)",
            "TOTAL ANNUAL COSTS",
            ("Annual Maximum", "Import Electr."),
            ("Annual", "Balance3 Heat"),
            ("Annual Minimum", "Stabil. Load"),
        )

        reductionInvestmentCost = np.round(
            ((self.largeValueOfBoiler - maxBoiler3) *
            self.boilerCostInMDDK * self.interest) / \
                (1 - np.pow((1 + self.interest), - self.boilerLifeTime)) + \
                    ((self.largeValueOfPP - maxPP) * \
                     self.PPCostInMDKK * self.interest) / \
                        (1 - np.pow((1 + self.interest), - self.PPLifeTime))
        )

        reduceFixedOMCost = np.round((
            (self.largeValueOfBoiler - maxBoiler3) *
             self.boilerCostInMDDK * self.fixedMOForBoilerinPercentage) + \
            ((self.largeValueOfPP - maxPP) *
             self.PPCostInMDKK * self.fixedMOForPPinPercentage))

        actualAnnualCost = Y[:, 1] - reductionInvestmentCost - \
            reduceFixedOMCost

        # The CO2 emissions are set directly from the results files, whereas
        # the cost is adjusted by the reduction in investment and fixed O&M
        # for the cases where CHP > PP.
        out["F"] = np.column_stack([
            Y[:, 0],
            np.where(mask, Y[:, 1], actualAnnualCost)
        ])

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
