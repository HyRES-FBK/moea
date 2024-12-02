import numpy as np
from typing import Union, List
from itertools import product

from pymoo.core.sampling import Sampling


def delta():
    return np.random.rand()

def increasing(beta):
    return np.random.rand()**(1/(beta+1))


def decreasing(beta):
    return 1 - (1 - np.random.rand())**(1/(beta+1))


def generate_sample(problem, o, beta, dv):
    if problem.vars[f"dk{o}"].iloc[dv]:
        return increasing(beta)
    if not problem.vars[f"dk{o}"].iloc[dv]:
        return decreasing(beta)
    elif problem.vars[f"dk{o}"].iloc[dv] is None:
        return np.random.rand()


class DomainKnowledgeInitialization(Sampling):

    def __init__(self, betas: Union[List, np.ndarray]):
        super().__init__()
        if type(betas) is list:
            betas = np.array(betas)
        self.betas = betas

    def _do(self, problem, n_samples, **kwargs):

        o = problem.n_obj
        b = len(self.betas)
        d = problem.n_var
        n_c = b**d
        # The number of samples to be generated
        n_DK = o * n_c * n_samples
        # Create the matrix to store the samples
        X = np.zeros((n_DK, problem.n_var))

        # Iterate over the number of samples to be generated
        for i in range(n_samples):
            # Iterate over the number of objectives/knowledge domains
            for j in range(o):
                # Iterate over combinations of betas and variables
                for k in range(b):
                    # Iterate over variables
                    for dv in range(d):
                        X[i * (o * (n_c)) + j * (n_c) + k, dv] = \
                            generate_sample(problem, j, self.betas[k], dv)

        if problem.has_bounds():
            xl, xu = problem.bounds()
            assert np.all(xu >= xl)
            X = xl + (xu - xl) * X

        return X


if __name__ == '__main__':
    pass
