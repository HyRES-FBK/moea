def get_algorithm(name, *args, **kwargs):
    name = name.lower()

    from moea.algorithms.base_algorithm import BaseAlgorithm
    from moea.algorithms.mahbub2016 import Mahbub2016

    ALGORITHM = {
        'base_algorithm': BaseAlgorithm,
        'nsga2': BaseAlgorithm,
        'nsgaii': BaseAlgorithm,
        'nsga-ii': BaseAlgorithm,
        'mahbub2016': Mahbub2016,
    }

    if name not in ALGORITHM:
        raise ValueError(f"Algorithm {name} not found.")

    return ALGORITHM[name](*args, **kwargs)
