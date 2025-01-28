import re
import typer
import pickle
from loguru import logger

from pymoo.optimize import minimize

from moea.config import ENERGYPLAN_DATA_DIR
from moea.models import get_model
from moea.algorithms import get_algorithm


app = typer.Typer()


def find_version(file_path: str) -> str:
    version_pattern = re.compile(r'^version\s*=\s*[\'"]([^\'"]+)[\'"]', re.MULTILINE)
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            match = version_pattern.search(content)
            if match:
                return match.group(1)
            else:
                return "Version not found"
    except FileNotFoundError:
        return "File not found"


@app.command()
def version():
    """Show the version of the MOEA package"""
    # Parse version from the config.py file using regex
    typer.echo(f"MOEA {find_version('pyproject.toml')}")


# Add more commands as needed
@app.command()
def run(
    algorithm: str = typer.Argument(
        default="NSGA-II",
        help="The optimization algorithm."),
    model: str = typer.Argument(
        default="",
        help="The model to be optimized."),
    data_file: str = typer.Argument(
        default="",
        help="The reference data file in ``EnergyPLAN Data/Data`` folder."),
    pop_size: int = typer.Option(
        default=25,
        help="The population size."),
    n_gen: int = typer.Option(
        default=100,
        help="The number of generations used as stopping criterion.")
):
    """
    Run the optimization algorithm.
    """
    # TODO: Check if the data file is in ANSI format

    # Data file is in EnergyPLAN Data folder
    data_file = ENERGYPLAN_DATA_DIR / data_file

    # Import the model dynamically
    if not data_file.exists():
        problem = get_model(model, data_file)
    else:
        problem = get_model(model)

    # Import the algorithm dynamically
    algorithm = get_algorithm(algorithm, pop_size=pop_size)

    logger.info(f"Running {algorithm} on {model}.")

    res = minimize(
        problem=problem,
        algorithm=algorithm,
        termination=('n_gen', n_gen),
        verbose=True,
        save_history=True
    )

    logger.info("Optimization finished.")

    # Save the results
    with open(f"results_{model}_{algorithm}.pkl", "wb") as f:
        pickle.dump(res, f)

    logger.info("Results saved.")


if __name__ == "__main__":
    app()
