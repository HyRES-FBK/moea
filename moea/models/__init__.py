def get_model(name, *args, **kwargs):
    name = name.lower()

    from moea.models.aalborg import AalborgA, AalborgB
    from moea.models.giudicarie import GiudicarieEsteriori

    PROBLEM = {
        'aalborga': AalborgA,
        'aalborgb': AalborgB,
        'giudicarie': GiudicarieEsteriori,
    }

    if name not in PROBLEM:
        raise ValueError(f"Problem {name} not found.")

    return PROBLEM[name](*args, **kwargs)