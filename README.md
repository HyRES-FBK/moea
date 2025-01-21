# :dna: MOEA for Energy Scenario Optimization

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

The repositoty collects energy scenario optimization case studies using multi-
objective evolutionary algorithms (MOEA).
Energy modelling is delegated to EnergyPLAN, which is used here as the
the objective function.
The code ease the interaction with EnergyPLAN and allows the user to focus on
pre- and post-processing of data for energy modelling and optimization.

For further details about the code, check the complete
[documentation](https://moea-2a642b.pages.fbk.eu/).

## :page_with_curl: Requirements

The MOEA package works only in Windows because EnergyPLAN runs only in Windows.

EnergyPLAN is provided with the repository and no separate download is
required.
If you want to use a different version of EnergyPLAN, you can change the folder
named ``EnergyPLAN``.


Be aware that EnergyPLAN requires to respect a specific folder structure.
Since the MOEA exploits EnergyPLAN's *spool* mode, check for the existence of
the folders ``spool`` and ``spool/results``.

The only requirement of the project is to have **conda** available to generate
a Python environment.
Conda is availabale both through [Anaconda](https://www.anaconda.com/download)
or [Miniconda](https://docs.anaconda.com/miniconda/install/).

## :rocket: Quickstart

To get started, create a conda environment via

```bash
cd <MOEA-project-folder>
conda env create -f environment.yml
```

and remember to activate it using the command

```bash
conda activate moea
```

### :movie_camera: Scenario generation

Setup of an experiment is carried out in EnergyPLAN, which provides a handy GUI.
When a scenario has been configured, experimental parameters are stored in a
data file, whose path is required to run the algorithm. Input data files
generated with EnergyPLAN are stored in ``EnergyPLAN/EnergyPLAN Data/Data``.
The set decision variables that can be used in MOEA algorithm is a subset of
the parameters in the input file.
The algorithms will change only the variables declared in the model,
leaving all the others unchanged.

### :sparkles: Model definition

The word *model* is used to indicate the problem to be optimized.
This means that:

1. Problem variables are declared within the model. They do not necessarily
have to map to an EnergyPLAN input value, they can also be calculated starting
from EnergyPLAN inputs.
2. Objective function values are declared in a model and they can either be
EnergyPLAN output values, or they can result from postprocessing of EnergyPLAN
solution values.
3. Constraints are declared in the model file.

It is good practice to store models in the folder ``moea/models``.
To create a new model, declare a new class that inherits from the ``BaseModel``
class in ``moea.models.base_model``.
Each module (i.e., a file in the folder ``models``) can contain several models.
A good practice is to group models in modules by similarity of the concepts
that they are intended to model.

When a new model is created, to make it available to the function
``get_model``, it must be added to the list of models in the ``__init__.py``
file of the ``models`` package.

### :toolbox: Algorithm definition

Custom algorithms can be defined by the user.
New algorithms can inherit from existing algorithms and modify only specific
functions.
For example, the Domain Knowledge algorithm by Mahbub inherits from the class
``BaseAlgorithm``, which in turn inherits from an ``NSGA2`` algorithm, and
modifies only the population initialization and mutation functions.

It is good practice to store algorithms in the folder ``moea/algorithms``.

When a new algorithm is created, to make it available to the function
``get_algorithm``, it must be added to the list of models in the
``__init__.py`` file of the ``algorithms`` package.

### :man_biking: Run an MOEA algorithm

If the Python environment was created without errors, the application ``moea``
should be accessible from the command line when the environment is active.

A minimal guide to the use of ``moea`` is available via

```bash
moea --help
```

and help for each of the command can be consulted using

```bash
moea COMMAND --help
```

The ``run`` command requires three (mandatory) arguments

1. the name of the algorithm, which must correspond to the name of the
algorithm class,
2. the name of the model to be optimized, which must correspond to the name
of the model class, and
3. the name of the file containing the parameters for a scenario
(w/o the ``.txt`` extension does not matter).
4. Optionally, the population size can be set using the flag ``--pop-size``
followed by a positive integer number.
5. Optionally, the number of iterations can be set using the flag ``--n-gen``
followed by a positive integer number.

The syntax of the command is the following

```bash
moea run ALGORITHM MODEL DATA_FILE_NAME --pop-size 10 --n-iter 10
```

which runs the algorithm with a population size of 10 for 10 generations.
The list of optional MOEA parameters, e.g., number of individuals in the
initial population, number of generations, etc., can be listed using the
``--help`` flag for the ``run`` command.

## :briefcase: Project Organization

```
├── LICENSE            <- Open-source license if one is chosen.
├── Makefile           <- Makefile with convenience commands like `make data` or `make train`.
├── README.md          <- The top-level README for developers using this project.
│
├── EnergyPLAN
│   ├── EnergyPLAN Data <- EnergyPLAN data folder, which contains subfolders ``Costs``, ``Data``, and ``Distributions``.
│   ├── EnergyPLAN Help <- EnergyPLAN documentation.
│   ├── EnergyPLAN Tools
│   ├── energyPLAN.exe  <- EnergyPLAN executable.
│   ├── energyPLAN.ini
│   └── spool           <- The folder where to save the input files corresponding to MOEA solutions.
│       └── results     <- The folder where EnergyPLAN saves results files when executed in ``spool`` mode.
│
├── docs                <- A Jupyter book project containing both MOEA documentation and case studies description.
│
├── notebooks           <- Jupyter notebooks. Naming convention is a number (for ordering),
│                          the creator's initials, and a short `-` delimited description, e.g.
│                          `1.0-jqp-initial-data-exploration`.
│
├── pyproject.toml      <- Project configuration file with package metadata for
│                          moea and configuration for tools like black.
│
├── environment.yml     <- The requirements file for reproducing the analysis environment, e.g.
│                          generated with `conda env create -f environment.yml`.
│
└── moea                <- Source code for use in this project.
    │
    ├── __init__.py             <- Makes moea a Python module.
    │
    ├── config.py               <- Store useful variables and configuration.
    │
    ├── cli.py                  <- The command line interface app.
    │
    ├── utils.py                <- Utility function to call EnergyPLAN and much more.
    │
    ├── models
    │   ├── __init__.py
    │   ├── base_model.py       <- Code for the ``BaseModel`` class.
    │   └── ...                 <- Code for all other models.
    │
    ├── algorithms
    │   ├── __init__.py
    │   ├── base_algorithm.py   <- Code for the ``BaseAlgorithm`` class.
    │   └── ...                 <- Code for all other algorihtms.
    │
    └── plots.py                <- Code to create visualizations.
```

--------

