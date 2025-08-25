from moea.models.aalborg import Aalborg
from moea.models.giudicarie import GiudicarieEsteriori
from moea.models.vdn import ValDiNon
from moea.models.ceis2021 import CEIS2021


MODELS = {
    'aalborg': Aalborg,
    'giudicarie': GiudicarieEsteriori,
    'vdn': ValDiNon,
    'ceis2021': CEIS2021
}


def get_model(name, *args, **kwargs):
    name = name.lower()

    if name not in MODELS:
        raise ValueError(f"Problem {name} not found.")

    return MODELS[name](*args, **kwargs)