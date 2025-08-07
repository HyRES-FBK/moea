def get_model(name, *args, **kwargs):
    name = name.lower()

    from moea.models.aalborg import Aalborg
    from moea.models.giudicarie import GiudicarieEsteriori
    from moea.models.vdn import ValDiNon
    from moea.models.ceis2021 import CEIS2021

    PROBLEM = {
        'aalborg': Aalborg,
        'giudicarie': GiudicarieEsteriori,
        'vdn': ValDiNon,
        'ceis2021': CEIS2021
    }

    if name not in PROBLEM:
        raise ValueError(f"Problem {name} not found.")

    return PROBLEM[name](*args, **kwargs)