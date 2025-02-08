def get_model(name, *args, **kwargs):
    name = name.lower()

    from moea.models.aalborg import Aalborg
    from moea.models.giudicarie import GiudicarieEsteriori
    from moea.models.vdn import ValDiNon

    PROBLEM = {
        'aalborg': Aalborg,
        'giudicarie': GiudicarieEsteriori,
        'vdn': ValDiNon
    }

    if name not in PROBLEM:
        raise ValueError(f"Problem {name} not found.")

    return PROBLEM[name](*args, **kwargs)