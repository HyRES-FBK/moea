# Get started

The MOEA packege is a command line interface (CLI) tool.
The [Usage](usage.md) guide documents the instrucitons to run the algorithm.

## Installation

The preferred environment to run the MOEA tool is via conda.
All the code snippets in the following are executed in command line prompt
(CMD, PowerShell, etc.) from the projecet folder.

```{admonition}
If you decide to use Anaconda, please be sure to add it to the system PATH,
otherwise you will not be able to call it from the command line when creating
the environment.

If you already installed Anaconda and want to add conda to the system PATH,
[this video](https://www.youtube.com/watch?v=fGbuwGCtDl4) provides you the solution.
```

```{admonition}
Anaconda does not always works properly with PowerShell. If you are having
troubles with PowerShell, please use the Command Prompt or `cmd`.
```

### Requirements

- The code runs only in **Windows OS** due to EnergyPLAN incompatibility with
other OSs.
- Anaconda or Miniconda for the creation of a Python virtual environment.

### Create a conda environment

To create a new conda environment, use the following command:

```sh
conda env create -f environment.yml
```

With the command above, you created a Python virtual environment whose name is
``moea``.

### Activate the environment

Activate the newly created environment with:

```sh
conda activate moea
```

### Installation via ``pip``

Alternatively, you check the ``environment.yml`` file and setup your own
enviroment manually using ``pip``. In this latter case remember to install the
``moea`` package using ``pip install -e .``.

## Usage

To test that the installation process was completed successfully, try to run
the following command in the command prompt with the ``moea`` environment
activated

```sh
moea --version
```

and you should receive a message similat to

```sh
2024-10-22 12:23:25.506 | INFO     | moea.config:<module>:11 - PROJ_ROOT path is: C:\<paht to moea>\moea
MOEA 0.0.1
```

This means that the installation process was completed successfully.

### Run an example case

Try to run the Aalborg case with a limited population size and for a low
number of generations.

```sh
moea run nsga-ii Aalborg Aalborg2050_2objectives.txt --pop-size 5 --n-gen 5
```

During the execution, an EnergyPLAN window will pop-up and disappear as many
times as the number of generations. This may affect the usability of your pc
during the execution.

The output should be similar to what follows.

```sh
2024-10-22 12:31:35.662 | INFO     | moea.config:<module>:11 - PROJ_ROOT path is: C:\<path to moea>\moea
2024-10-22 12:31:36.275 | INFO     | moea.cli:run:59 - Running BaseAlgorithm on aalborga.
==========================================================================================
n_gen  |  n_eval  | n_nds  |     cv_min    |     cv_avg    |      eps      |   indicator
==========================================================================================
     1 |        5 |      2 |  0.000000E+00 |  0.1900000000 |             - |             -
     2 |       10 |      4 |  0.000000E+00 |  0.0120000000 |  0.0037878788 |         ideal
     3 |       15 |      4 |  0.000000E+00 |  0.000000E+00 |  0.0221385388 |             f
     4 |       20 |      5 |  0.000000E+00 |  0.000000E+00 |  0.0688379527 |             f
     5 |       25 |      5 |  0.000000E+00 |  0.000000E+00 |  0.0522066738 |         ideal
2024-10-22 12:32:27.628 | INFO     | moea.cli:run:68 - Optimization finished.
2024-10-22 12:32:27.631 | INFO     | moea.cli:run:74 - Results saved.
```

A detailed explanation of the ``run`` command syntax is providede in the
[Usage section](usage.md).