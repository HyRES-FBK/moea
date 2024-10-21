def get_algorithm(name, *args, **kwargs):
    name = name.lower()

    from moea.algorithms.base_algorithm import BaseAlgorithm

    ALGORITHM = {
        'base_algorithm': BaseAlgorithm,
        'nsga2': BaseAlgorithm,
        'nsgaii': BaseAlgorithm,
        'nsga-ii': BaseAlgorithm,
    }

    if name not in ALGORITHM:
        raise ValueError(f"Algorithm {name} not found.")

    return ALGORITHM[name](*args, **kwargs)
