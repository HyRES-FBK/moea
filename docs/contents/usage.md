---
authors:
  - name: Michele Urbani
    affiliation: Fondazione Bruno Kessler
    department: Sustainable Energy Center
---
# MOEA Usage

Setup of an experiment is carried out in EnergyPLAN, which provides a handy GUI.
When a scenario has been configured, experimental parameters are stored in a data file, which path is required to run the algorithm.
The decision variables are a subset of the parameters in the input file and the algorithms will change only those values, leaving all the other parameters unchanged.

## Define a model

The word model is used to indicate the problem to be optimized, which is an model of reality defined by the user.
A new model should be declared in a new file in the folder ``moea/models``.
Each module (i.e., a file in the folder ``models``) can contain several models.
To create a new model, declare a new class that inherits from the ``BaseModel`` class in ``moea.models.base_model``.
A good practice is to group models in modules by similarity of the concepts that they are intended to model.

When a new model is created, to make it available to the function ``get_model``, it must be added to the list of models in the ``__init__.py`` file of the ``models`` package.

## Define an algorithm (optional) (work in progress)

Custom algorithms can be defined by the user.

    TODO...

The list of available algorithms is

```bash
PS> moea list-algorithms
```

When a new algorithm is created, to make it available to the function ``get_algorithm``, it must be added to the list of models in the ``__init__.py`` file of the ``algorithms`` package.

## MOEA interface

A user can interact with the MOEA via CLI or declaratively in a script.
CLI is practical when several runs of the same optimization problems are
required and we want to automate this task.
Interaction via scripting is the preffered way when developing a new model of
an energy system, e.g., to run the algorithm from a script, or when using the
MOEA in a Jupyter notebook.

### Command line interface

If the Python environment was created without errors, the application ``moea`` should be accessible from the command line when the environment is active.

A minimal guide to the use of ``moea`` is available via

```bash
PS> uv run moea --help
```

and help for each of the command can be consulted using

```bash
PS> uv run moea COMMAND --help
```

#### Run the algorithm

The ``run`` command requires three (mandatory) arguments

1. the name of the algorithm, which must correspond to the name of the algorithm class,
2. the name of the model to be optimized, which must correspond to the name of the model class, and
3. the name of the file containing the parameters for a scenario (w/o the ``.txt`` extension does not matter).

The syntax of the command is the following

```bash
PS> uv run moea run ALGORITHM MODEL DATA_FILE_NAME
```
which runs the algorithm with default parameters.
The list of optional MOEA parameters, e.g., number of individuals in the initial population, number of generations, etc., can be listed using the ``--help`` flag for the ``run`` command.

### Declarative approach

The declarative approach requires at least to:
1. Recall (or declare a new) problem class and initialize it;
2. Recall (or declare a new) algorithm class and initialize it;
3. Run the algorithm using the PyMOO function `minimize`.

#### Declare a new problem

```python
import pandas as pd

from moea.models.base_model import BaseModel
from moea.energyplan.energyplan163 import EnergyPLAN163


class MyModel(BaseModel):

    energyplan_version = EnergyPLAN163

    def __init__(self, data_file: str | Path, **kwargs):
        # Define variables here

        self.vars = pd.DataFrame(
            columns=['name', 'lb', 'ub']
        )

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
        self.energyplan.run(
            inputs=...
        )

        # Parse the output file
        Y = self.energyplan.read_values(
            "CO2-emission (corrected)",
            "TOTAL ANNUAL COSTS",
            ("Maximum", "import"),
            ("Annual", "heat3- balance"),
            ("Minimum", "stab.- load"),
        )

        # Store objective function values
        out["F"] = np.array(Y[:, :2])

        import_constr = ...

        heat_constr = ...

        out["G"] = np.column_stack([
            import_constr,
            stable_load,
        ])

```

#### Declare a new algorithm

#### Optimize using `minimize`
