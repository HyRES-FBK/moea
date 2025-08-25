from moea.algorithms.base_algorithm import BaseAlgorithm
from moea.algorithms.mahbub2016 import Mahbub2016


ALGORITHMS = {
    'base_algorithm': BaseAlgorithm,
    'nsga2': BaseAlgorithm,
    'nsgaii': BaseAlgorithm,
    'nsga-ii': BaseAlgorithm,
    'mahbub2016': Mahbub2016,
}


def get_algorithm(name, *args, **kwargs):
    name = name.lower()

    if name not in ALGORITHMS:
        raise ValueError(f"Algorithm {name} not found.")

    return ALGORITHMS[name](*args, **kwargs)
