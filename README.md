# :ship: MANTHOVA

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

The repository for the MANTHOVA project.

The framework proposed in this repository aims to simplify the interaction of users with
EnergyPLAN through Python when developing optmization algorithms.

For further details about the code, check the complete [documentation](https://moea-hyres-manthova-27756fd0bc31e2b80342f831b767e46e0413086846e.pages.fbk.eu/).

## :page_with_curl: Requirements

The MOEA package works only in Windows because EnergyPLAN runs only in Windows.

EnergyPLAN is provided with the repository and no separate download is required.
If you want to use a different version of EnergyPLAN, you can substitute the folder
named ``EnergyPLAN`` ensuring that the folder structure remains the same and that
the folders ``spool`` and ``spool/results`` exist.

The only requirement of the project is to have Conda available to generate a Python environment.

## :rocket: Quickstart

To get started, create a conda environment via

```bash
conda env create -f environment.yml
```

and remember to activate it using the command

```bash
conda activate manthova
```

### :movie_camera: Scenario generation

Setup of an experiment is carried out in EnergyPLAN, which provides a handy GUI.
When a scenario has been configured, experimental parameters are stored in a data file, which path is required to run the algorithm.
The decision variables are a subset of the parameters in the input file and the algorithms will change only those values, leaving all the other parameters unchanged.

### :sparkles: Define a model

Here the word model is used to indicate the problem to be optimized, which is an user-defined model of reality.
Models are declared in the folder ``moea/models``.
To create a new model, declare a new class that inherits from the ``BaseModel`` class in ``moea.models.base_model``.
Each module (i.e., a file in the folder ``models``) can contain several models.
A good practice is to group models in modules by similarity of the concepts that they are intended to model.

When a new model is created, to make it available to the function ``get_model``, it must be added to the list of models in the ``__init__.py`` file of the ``models`` package.

### Define an algorithm (optional) (work in progress)

Custom algorithms can be defined by the user.

    TODO...

If you want to use one of the available algorithm, you can browse the list of available algorithms using the command

```bash
moea algorithms
```

When a new algorithm is created, to make it available to the function ``get_algorithm``, it must be added to the list of models in the ``__init__.py`` file of the ``algorithms`` package.

### Run an MOEA algorithm

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

## :briefcase: Project Organization

```
├── LICENSE            <- Open-source license if one is chosen
├── Makefile           <- Makefile with convenience commands like `make data` or `make train`
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── external       <- Data from third party sources.
│   ├── interim        <- Intermediate data that has been transformed.
│   ├── processed      <- The final, canonical data sets for modeling.
│   └── raw            <- The original, immutable data dump.
│
├── docs               <- A default mkdocs project; see www.mkdocs.org for details
│
├── models             <- Trained and serialized models, model predictions, or model summaries
│
├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
│                         the creator's initials, and a short `-` delimited description, e.g.
│                         `1.0-jqp-initial-data-exploration`.
│
├── pyproject.toml     <- Project configuration file with package metadata for
│                         moea and configuration for tools like black
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials.
│
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures        <- Generated graphics and figures to be used in reporting
│
├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
│                         generated with `pip freeze > requirements.txt`
│
├── setup.cfg          <- Configuration file for flake8
│
└── moea   <- Source code for use in this project.
    │
    ├── __init__.py             <- Makes moea a Python module
    │
    ├── config.py               <- Store useful variables and configuration
    │
    ├── dataset.py              <- Scripts to download or generate data
    │
    ├── features.py             <- Code to create features for modeling
    │
    ├── modeling
    │   ├── __init__.py
    │   ├── predict.py          <- Code to run model inference with trained models
    │   └── train.py            <- Code to train models
    │
    └── plots.py                <- Code to create visualizations
```

--------

