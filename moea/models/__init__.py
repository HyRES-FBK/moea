def get_model(name, *args, **kwargs):
    name = name.lower()

    from moea.models.manhub2016 import Manhub2016

    PROBLEM = {
        'manhub2016': Manhub2016,
    }

    if name not in PROBLEM:
        raise ValueError(f"Problem {name} not found.")

    return PROBLEM[name](*args, **kwargs)