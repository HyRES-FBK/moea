def get_model(name, *args, **kwargs):
    name = name.lower()

    from moea.models.base_model import BaseProblem

    PROBLEM = {
        'base_model': BaseProblem,
    }

    if name not in PROBLEM:
        raise ValueError(f"Problem {name} not found.")

    return PROBLEM[name](*args, **kwargs)