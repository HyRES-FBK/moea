import numpy as np
from pymoo.core.sampling import Sampling

from moea.models.giudicarie import GiudicarieEsteriori


class DirichletSampling(Sampling):

    def __init__(self):
        super().__init__()

    def _do(self, problem, n_samples, **kwargs):
        if problem is GiudicarieEsteriori:
            # Variable 0 is samplied uniformly
            v0 = np.random.uniform(problem.vars['PVCapacity']['lb'],
                                   problem.vars['PVCapacity']['ub'],
                                   size=(n_samples, 1))
            # Variables 1 to 5 must sum to one
            v1to5 = np.random.dirichlet(np.ones(5), size=(n_samples, 1))
            return np.hstack((v0, v1to5))
        else:
            raise NotImplementedError(
                f'{problem.__class__.__name__} does not match any model.'
            )
