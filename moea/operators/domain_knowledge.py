import numpy as np
from typing import Union, List

from pymoo.core.sampling import Sampling
from pymoo.core.mutation import Mutation
from pymoo.core.variable import get, Real
from pymoo.operators.crossover.binx import mut_binomial
from pymoo.operators.repair.to_bound import set_to_bounds_if_outside


def delta():
    return np.random.rand()


def increasing(beta):
    return np.random.rand()**(1 / (beta + 1))


def decreasing(beta):
    return 1 - (1 - np.random.rand())**(1 / (beta + 1))


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
        d = problem.n_var
        # Number of beta vectors to be generated
        N = 1000
        # Create the matrix to store the samples
        X = np.zeros((n_samples * o * N, problem.n_var))

        # Iterate over the number of samples to be generated
        for i in range(n_samples):
            # Iterate over the number of objectives/knowledge domains
            for j in range(o):
                # Generate 1000 samples of beta vectors of length d
                beta_samples = np.random.randint(len(self.betas) - 1,
                                                 size=(N, d))
                # Iterate over the number of beta vectors
                for k in range(len(beta_samples)):
                    # Generate the samples for the current beta vector
                    for dv in range(d):
                        X[i * (o * N) + j * N + k, dv] = generate_sample(
                            problem, j, self.betas[beta_samples[k, dv]], dv
                        )
        if problem.has_bounds():
            xl, xu = problem.bounds()
            assert np.all(xu >= xl)
            X = xl + (xu - xl) * X

        # Pick n_samples samples from the generated samples
        X = X[np.random.choice(X.shape[0], n_samples, replace=False), :]
        return X


def mut_pm(X, xl, xu, eta, prob, at_least_once):
    n, n_var = X.shape
    assert len(eta) == n
    assert len(prob) == n

    Xp = np.full(X.shape, np.inf)

    mut = mut_binomial(n, n_var, prob, at_least_once=at_least_once)
    mut[:, xl == xu] = False

    Xp[:, :] = X

    _xl = np.repeat(xl[None, :], X.shape[0], axis=0)[mut]
    _xu = np.repeat(xu[None, :], X.shape[0], axis=0)[mut]

    X = X[mut]
    eta = np.tile(eta[:, None], (1, n_var))[mut]

    delta1 = (X - _xl) / (_xu - _xl)
    delta2 = (_xu - X) / (_xu - _xl)

    mut_pow = 1.0 / (eta + 1.0)

    rand = np.random.random(X.shape)
    mask = rand <= 0.5
    mask_not = np.logical_not(mask)

    deltaq = np.zeros(X.shape)

    xy = 1.0 - delta1
    val = 2.0 * rand + (1.0 - 2.0 * rand) * (np.power(xy, (eta + 1.0)))
    d = np.power(val, mut_pow) - 1.0
    deltaq[mask] = d[mask]

    xy = 1.0 - delta2
    val = 2.0 * (1.0 - rand) + 2.0 * (rand - 0.5) * (np.power(xy, (eta + 1.0)))
    d = 1.0 - (np.power(val, mut_pow))
    deltaq[mask_not] = d[mask_not]

    # mutated values
    _Y = X + deltaq * (_xu - _xl)

    # back in bounds if necessary (floating point issues)
    _Y[_Y < _xl] = _xl[_Y < _xl]
    _Y[_Y > _xu] = _xu[_Y > _xu]

    # set the values for output
    Xp[mut] = _Y

    # in case out of bounds repair (very unlikely)
    Xp = set_to_bounds_if_outside(Xp, xl, xu)

    return Xp


class RenewableEnergyFavourMutation(Mutation):

    def __init__(self, prob=0.9, eta=20, at_least_once=False, **kwargs):
        super().__init__(prob=prob, **kwargs)
        self.at_least_once = at_least_once
        self.eta = Real(eta, bounds=(3.0, 30.0), strict=(1.0, 100.0))

    def _do(self, problem, X, params=None, **kwargs):
        X = X.astype(float)

        eta = get(self.eta, size=len(X))
        prob_var = self.get_prob_var(problem, size=len(X))

        Xp = mut_pm(X, problem.xl, problem.xu, eta, prob_var, at_least_once=self.at_least_once)

        return Xp


class REFM(RenewableEnergyFavourMutation):
    pass


class ConventionalEnergyFavourMutation():
    pass


class CEFM(ConventionalEnergyFavourMutation):
    pass


if __name__ == '__main__':
    pass
