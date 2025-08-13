import subprocess
import numpy as np
import pandas as pd
from typing import Union, List
from pathlib import Path


ENERGYPLAN_EXE = "."
ENERGYPLAN_SPOOL = "spool"
ENERGYPLAN_RESULTS = "results"

"""
All utility functions are defined here.
"""


def solow_polasky_diversification(X: np.ndarray,
                                  theta: float,
                                  size: int
                                  ) -> np.ndarray:
    """
    Returns the set of solutions with cardinality equal to ``size`` that
    maximize the Solow-Polasky metric for a given population of solutions
    ``X``.

    Parameters
    ----------
    - ``X`` : np.ndarray
        The population of solutions. Rows are solutions, columns are decision
        variables.
    - ``theta`` : float
        The normalizing scalar for the Solow-Polasky metric.
    - ``size`` : int
        The number of solutions to be selected.

    Returns
    -------
    - np.ndarray
        The selected solutions.
    """
    assert X.shape[0] > size
    # Create a copy of the population to remove solutions iteratively
    Xp = np.zeros((1, X.shape[1]))
    # Copy the first solution
    Xp[0] = X[0]
    # Remove the first solution from the population
    X = X[1:]
    # Compute the distance of each solution to the selected population
    r = np.linalg.norm(X - np.repeat(Xp, X.shape[0], axis=0), axis=1)
    # Add the solution with the maximum distance to the selected population
    Xp = np.vstack((Xp, X[np.argmax(r)]))
    # Remove the selected solution from the population
    X = np.delete(X, np.argmax(r), axis=0)
    # Add individuals
    for i in range(1, size):
        Q = np.linalg.norm(Xp[:, None] - Xp[None, :], axis=-1)
        Q = np.exp(- theta * Q)
        Qinv = np.linalg.inv(Q)
        sp = np.zeros(X.shape[0])
        # Evaluate candidates
        for j in range(X.shape[0]):
            # Calculate the contribution of the candidate to the diversity
            # of the population
            r = np.linalg.norm(Xp - np.repeat(X[j, None], Xp.shape[0], axis=0),
                               axis=1)
            v = - r.T @ Qinv @ r
            W = Qinv @ r
            phi = np.sum(W)
            sp[j] = (1 / v) * np.pow(phi - 1, 2)
        # Move the individual with the highest diversity contribution to the
        # selected population
        Xp = np.vstack((Xp, X[np.argmax(sp)]))
        # Remove the selected individual from the population
        X = np.delete(X, np.argmax(sp), axis=0)
    return Xp


def execute_energyplan(input_file: Union[str, Path],
                       output_file: Union[str, Path],
                       energy_plan_path: Union[str, Path] = ENERGYPLAN_EXE
                       ) -> None:
    """
    Execute EnergyPLAN with the input vector as input and read the output
    vector from a file.
    """
    subprocess.run([str(energy_plan_path),
                    "-i", str(input_file),
                    "-ascii", str(output_file)])


def execute_energyplan_spool(input_files: List[Union[str, Path]]) -> None:
    """
    Execute EnergyPLAN in spool mode.

    The spool mode is used to run EnergyPLAN in batch mode. The input files
    are passed as arguments to the executable and the output is written to
    to a file with the same name as the input file stored in the folder
    ``spool/results`` within the EnergyPLAN directory. The spool number is
    automatically assigned equal to the number of files passed as input.

    Parameters
    ----------
    input_files : list of str or Path
        List of input file names to be used by EnergyPLAN.
    """
    subprocess.run([str(ENERGYPLAN_EXE),
                    "-spool", str(len(input_files)),
                    *[str(f) for f in input_files],
                    "-ascii", "run"])


def parse_output(output_file: Union[str, Path]) -> dict:
    """
    Parse the output file of EnergyPLAN and return the data in a dictionary.
    Sections are found by looking for specific keywords in the file and then
    they are stored in the dictionary as pandas Series or DataFrames.
    """

    with open(output_file, 'r', encoding='latin-1') as f:
        rows = f.readlines()

    output = {}

    # The output starts after warnings. Look for the word 'EnergyPLAN'
    for first_row, r in enumerate(rows):
        if 'EnergyPLAN' in r:
            break

    data = [r.split('\t') for r in rows[first_row:first_row + 76]]
    data = [[c.strip() for c in r] for r in data]

    # CALCULATION INFORMATION
    r = first_row + 2
    output['CALCULATION'] = pd.Series({i[0]: i[1] for i in data[r: r + 5]})

    # ANNUAL CO2 EMISSIONS (Mt)
    r += 7
    output[data[r][0].replace(':', '')] = \
        pd.Series({i[0]: i[1] for i in data[r + 1:r + 4]})

    # SHARE OF RES
    r += 4
    output[data[r][0].replace(':', '')] = \
        pd.Series({i[0]: i[1] for i in data[r + 1:r + 4]})

    # ANNUAL FUEL CONSUMPTIONS
    r += 5
    output[data[r][0]] = pd.DataFrame(
        data=[col[:3] for col in data[r + 1:r + 12]],
        columns=[None] + [col.replace(':', '') for col in data[r][1:3]]
    ).set_index(None)

    # ANNUAL COSTS (M DKK)
    r += 14
    output[data[r][0]] = pd.DataFrame(
        data=[col[:4] for col in data[r + 1:r + 30]],
        columns=[None] + [col.replace(':', '') for col in data[r][1:4]]
    ).set_index(None).replace('', pd.NA).dropna(how='all')

    # COSTS
    # Retrieve column names
    r = first_row - 1
    start, end = 7, 15
    columns = [i[start:end] for i in data[r:r + 2]]
    # Join first and second part of column names
    columns = [columns[0][i].strip() + ' ' + columns[1][i].rstrip()
               for i in range(len(columns[0]))]
    # Filter out empty values
    columns = [c for c in columns if c.strip()]

    # Clean data
    rawdata = [[col.strip().replace(',', '.') for col in row[start - 1:end]]
               for row in data[r + 2:r + 69]]
    # Filter out section separators and empty rows
    rawdata = [i for i in rawdata if len(i) > 1]
    # Drop empty values in rows
    rawdata = [[col for col in row if col] for row in rawdata]
    # Add empty values to obtain 8-columns rows
    data = []
    for row in rawdata:
        if len(row) < len(columns):
            row.extend([''] * (len(columns) - len(row)))
        data.append(row)
    # Create the dataframe
    df = pd.DataFrame(
        data=data,
        columns=[None] + columns,
    ).set_index(None)

    output['COSTS'] = df

    # Read column names for the annual, monthtly, and hourly values.
    # Names are split over rows 81 and 82 and need to be recombined.
    start, end = first_row + 77, first_row + 79
    columns = [r.split('\t') for r in rows[start: end]]
    assert len(columns[0]) == len(columns[1])
    # Join first and second part of column names
    columns = [columns[0][i].strip() + columns[1][i].rstrip()
               for i in range(len(columns[0]))]
    # Filter out empty values
    columns = [c for c in columns if c]

    # Read annual, monthly, and hourly values
    data = [r.split('\t') for r in rows[first_row + 81:]]
    # Clean data
    data = [[col.strip().replace(',', '.') for col in row] for row in data]
    # Filter out section separators and empty rows
    data = [i for i in data if len(i) > 1]
    # Drop empty values in rows
    data = [[col for col in row if col] for row in data]
    # Create the dataframe
    df = pd.DataFrame(
        data=data,
        columns=[None] + columns,
    )
    # Set the first columns as index
    df.set_index(df.columns[0], inplace=True)

    # Split the dataframe and add to the output dictionary
    output['TOTAL FOR ONE YEAR (TWh/year)'] = df.iloc[0]
    output['MONTHLY AVERAGE VALUES (MW)'] = df.iloc[1:16]  # 12 months + 3 anual averages
    output['HOURLY VALUES (MW)'] = df[16:]

    return output


def parse_input(input_file: Union[str, Path]) -> dict:
    """
    Parse the input file of EnergyPLAN and return the data in a dictionary.
    """
    with open(input_file, 'r', encoding='utf-16') as f:
        rows = f.readlines()
    data = {}
    for i in range(0, len(rows), 2):
        if rows[i] == 'xxx':
            break
        data[rows[i].strip().replace('=', '')] = rows[i + 1].strip()
    return data


if __name__ == "__main__":
    pass
