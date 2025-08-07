# Get started

This short guide explains how to setup a Python environment and run a case study
from the Command Line Interface (CLI). When developing new energy models, it
could be desirable to work with Jupyter notebooks, which requires a declarative
use of functions and classes. See the [Usage](contents/usage.md) guide to learn
about this approach.

## Installation

```{admonition}
FBK users are no longer allowed to use the Anaconda suite due to the potential
infringement of the Anaconda Terms of Use. **Please do not use Anaconda**.
```

### Requirements

- The code runs only in **Windows OS** due to EnergyPLAN incompatibility with
other OSs.
- A Python interpreter >= 3.10. Consider using [uv](https://docs.astral.sh/uv/)
to manage Python environments.

### Install uv

uv can be installed autonomously by users with an FBK computer. The official
guide for the installation can be found
[here](https://docs.astral.sh/uv/getting-started/installation/).
Open Powershell and run the following command

```bash
PS> powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Create a Python virtual environment

To create a new Python environment with the required packages to run the
project, use the following command:

```bash
PS> uv sync
```

A new Python environment is created in the hidden folder `.venv` and all
required extensions are install with it, included the `moea` package.

### Activate the environment

The local Python virtual environment can be activated with the command

```sh
PS> .venv/Scripts/activate
```

and you should see `(moea)` before the `PS>` in your shell.
Alternatively, you can run a script prepending the command `uv run` to any
Python command. Using `uv run` guarantees that the correct Python environment
is used to run any script of the project.

## Usage

To test that the installation process was completed successfully, try to run
the following command in the command prompt with the ``moea`` environment
activated

```sh
(moea) PS> moea --version
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
moea run nsga-ii AalborgA Aalborg2050_2objectives.txt --pop-size 5 --n-gen 5
```

During the execution, an EnergyPLAN window will pop-up and disappear as many
times as the number of function evaluations. This may affect the usability of
your pc during the execution.

The standard output should be similar to what follows.

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