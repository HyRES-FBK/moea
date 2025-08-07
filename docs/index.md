# MOEA for energy scenario optimization

This repository reproduces a few case studies on multi-objective optimization
of multi-energy systems developed by members of the
[Sustainable Energy Centre](https://energy.fbk.eu/)
at the [Bruno Kessler Foundation](https://www.fbk.eu/en/).

The case studies reproduced here rely on the [EnergyPLAN](https://energyplan.eu/)
software, a simulator of the operation of national energy systems on an hourly
basis, including the electricity, heating, cooling, industry, and transport
sectors.

Multi-objective optimization algorithms are developed using
[PyMOO](https://pymoo.org/), a framework implementing state of the art single-
and multi-objective optimization algorithms and many more features related to
multi-objective optimization such as visualization and decision making.

## Reading guide

- The [Get started](contents/getting-started.md) page shows how to initialize
a Python environment, and optimize a case study from the command line.
- An in-depth guide to the declaration of models and the use of the optimizer
is provided in the [Usage section](contents/usage.md).
- The [Documentation](contents/documentation.md) page provides a complete guide
of the available models and algorithms.
- A collection of case studies help to get familiar with the use of the
optimization suite.
