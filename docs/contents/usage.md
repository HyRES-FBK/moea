
# MOEA Usage

Setup of an experiment is carried out in EnergyPLAN, which provides a handy GUI.
When a scenario has been configured, experimental parameters are stored in a data file, which path is required to run the algorithm.
The decision variables are a subset of the parameters in the input file and the algorithms will change only those values, leaving all the other parameters unchanged.

## :sparkles: Define a model

Here the word model is used to indicate the problem to be optimized, which is an user-defined model of reality.
Models are declared in the folder ``moea/models``.
To create a new model, declare a new class that inherits from the ``BaseModel`` class in ``moea.models.base_model``.
Each module (i.e., a file in the folder ``models``) can contain several models.
A good practice is to group models in modules by similarity of the concepts that they are intended to model.

When a new model is created, to make it available to the function ``get_model``, it must be added to the list of models in the ``__init__.py`` file of the ``models`` package.

## Define an algorithm (optional) (work in progress)

Custom algorithms can be defined by the user.

    TODO...

If you want to use one of the available algorithm, you can browse the list of available algorithms using the command

```bash
moea algorithms
```

When a new algorithm is created, to make it available to the function ``get_algorithm``, it must be added to the list of models in the ``__init__.py`` file of the ``algorithms`` package.

## Command line interface of MOEA

User interaction with the MOEA occurs via command line interface (CLI).

To browse the documentation of the MOEA package directly from the command line,
type ``moea --help``.

### Run the algorithm

If the Python environment was created without errors, the application ``moea`` should be accessible from the command line when the environment is active.

A minimal guide to the use of ``moea`` is available via

```bash
moea --help
```

and help for each of the command can be consulted using

```bash
moea COMMAND --help
```

The ``run`` command requires three (mandatory) arguments

1. the name of the algorithm, which must correspond to the name of the algorithm class,
2. the name of the model to be optimized, which must correspond to the name of the model class, and
3. the name of the file containing the parameters for a scenario (w/o the ``.txt`` extension does not matter).

The syntax of the command is the following

```bash
moea run ALGORITHM MODEL DATA_FILE_NAME
```

which runs the algorithm with default parameters.
The list of optional MOEA parameters, e.g., number of individuals in the initial population, number of generations, etc., can be listed using the ``--help`` flag for the ``run`` command.
