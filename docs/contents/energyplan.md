# EnergyPLAN

EnergyPLAN is software for energy planning at a regional, national, and supra-
national level.
It works on a yearly time span, which means that hourly time series of data and
distributions must be provided for one year.

## Command line interface

The EnergyPLAN integration with a MOEA is possible only by calling EnergyPLAN
via command line.
A complete guide to use EnergyPLAN via command line does not exist thogh.
In the following, we try to sketch a guide for the syntax used to call
EnergyPLAN from the command line.

```
<path-to-energyplan-folder>/EnergyPLAN.exe [OPTIONS] -i <input-file-path>
```

The options include:

- ``-ascii`` allows the user to provide the output file path.
- ``-m`` to provide a modification file that will overwrite some of the options
in a complete input file. It works only in combination with the ``-i`` options.

```{warning}
EnergyPLAN seems not to accept file names containing ``_`` or ``-``.
```

EnergyPLAN runs on a single case by default, and it opens and close the
graphical user interface at every call.
This is a clear bottleneck to multiple sequential executions.
Although it is not mentioned in the official guide, EnergyPLAN provides the
possibility to solve multiple instances within the same session.
This is the so-called *spool* mode.

### Spool mode

The spool mode can solve an array of models during the same session, i.e.
opening the graphical user interface only once.

To run EnergyPLAN using the spool mode, the following folder structure must be
respected.

```
EnergyPLAN/
    EnergyPLAN Data/
        ...
    EnergyPLAN Distributions/
        ...
    EnergyPLAN Tools/
        ...
    spool/
        input1.txt
        input2.txt
        ...
        inputN.txt
        results/
```

```{warning}
EnergyPLAN will not work if there is no ``spool`` folder and ``results``
folder within it.
```

The syntax of the command is only partly known and it works as follows.

```
<path-to-energyplan-folder>/EnergyPLAN.exe [OPTIONS] -spool N -i
<input-file-path1> [<input-file-path2> ...] -ascii run
```

where

- ``-spool`` is a mandatory argument and must be followed by the number of
input files ``N``.
- ``-i`` must be followed by at least one file and at most many files as your
OS's max path length allows you to prompt.
- ``ascii`` is mandatory and must be followed by the command ``run``.

As far as the author of this documents knows, it is not possible to provide
modification files when using the spool mode.
This means that input files must be written from scratch during an iteration.