import numpy as np
from typing import Union, List

from pymoo.core.sampling import Sampling
from pymoo.core.mutation import Mutation
from pymoo.core.callback import Callback
from pymoo.core.variable import get, Real
from pymoo.operators.mutation.pm import mut_pm
from pymoo.operators.crossover.binx import mut_binomial
from pymoo.operators.repair.to_bound import set_to_bounds_if_outside

from moea.utils import solow_polasky_diversification


def delta():
    return np.random.rand()


def increasing(beta):
    return np.random.rand()**(1 / (beta + 1))


def decreasing(beta):
    return 1 - (1 - np.random.rand())**(1 / (beta + 1))


def generate_sample(problem, o, beta, dv):
    if problem.vars[f"dk{o}"].iloc[dv] == True:
        return increasing(beta)
    if problem.vars[f"dk{o}"].iloc[dv] == False:
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
                beta_samples = np.random.choice(self.betas, size=(N, d))
                # Iterate over the number of beta vectors
                for k in range(len(beta_samples)):
                    # Generate the samples for the current beta vector
                    for dv in range(d):
                        X[i * (o * N) + j * N + k, dv] = generate_sample(
                            problem, j, beta_samples[k, dv], dv
                        )
        if problem.has_bounds():
            xl, xu = problem.bounds()
            assert np.all(xu >= xl)
            X = xl + (xu - xl) * X

        # Scale the samples in the range [0, 1]
        X = (X - problem.xl) / (problem.xu - problem.xl)

        # Pick n_samples individuals from the generated samples
        X = solow_polasky_diversification(X, theta=6.0, size=n_samples)

        # Rescale the samples back to the original range
        X = problem.xl + (problem.xu - problem.xl) * X
        return X


def modified_polynomial_mutation(X, xl, xu, eta, prob, dk, at_least_once):

    n, n_var = X.shape

    # Create a copy of the decision variables
    Xp = np.copy(X)

    # Define whether the mutation should be applied or not
    mut = mut_binomial(n, n_var, prob, at_least_once=at_least_once)
    # Exclude cases where the lower and upper bounds are the same
    mut[:, xl == xu] = False

    # Define the lower and upper bounds for the mutation
    _xl = np.repeat(xl[None, :], X.shape[0], axis=0)
    _xu = np.repeat(xu[None, :], X.shape[0], axis=0)

    eta = np.repeat(eta[:, None], X.shape[1], axis=1)

    # Define mutation power to ease readability
    mut_pow = 1.0 / (eta + 1.0)

    # Define random values to be used in the mutation process
    rand = np.random.random(X.shape)

    # Map domain knowledge to numerical values
    dk_values = np.zeros(dk.values.shape)
    for i in range(dk.values.shape[0]):
        if dk.values[i] == True:
            dk_values[i] = 1
        elif dk.values[i] == False:
            dk_values[i] = -1
        else:
            dk_values[i] = 0

    # Compute increasing variables
    deltaq = np.where(
        dk_values == 1,
        1 - (1 - rand + rand * np.pow(1 - ((_xu - X) / (_xu - _xl)),
                                      eta + 1)) ** mut_pow,
        rand
    )

    # Compute decreasing variables
    deltaq = np.where(
        dk_values == -1,
        - 1 + (rand + (1 - rand) * np.pow(1 - ((X - _xl) / (_xu - _xl)),
                                          eta + 1)) ** mut_pow,
        deltaq
    )

    # All the variables that are not increasing or decreasing are left as they
    # are since they were sampled randomly from a uniform distribution

    # # mutated values
    _Y = X + deltaq * (_xu - _xl)

    # back in bounds if necessary (floating point issues)
    _Y[_Y < _xl] = _xl[_Y < _xl]
    _Y[_Y > _xu] = _xu[_Y > _xu]

    # set the values for output
    Xp[mut] = _Y[mut]

    # in case out of bounds repair (very unlikely)
    Xp = set_to_bounds_if_outside(Xp, xl, xu)

    return Xp


class RenewableEnergyFavourMutation(Mutation):

    def __init__(self, prob=0.9, eta=20, dk_name="dk0", at_least_once=False,
                 **kwargs):
        """
        Parameters
        ----------
        - ``prob`` : float
            The probability of mutating a decision variable.

        - ``eta`` : float
            The mutation power.

        - ``dk_name`` : str
            The name of the column in the DataFrame that stores the domain
            knowledge.

        - ``at_least_once`` : bool
            Whether at least one decision variable should be mutated.

        - ``kwargs`` : dict
        """
        super().__init__(prob=prob, **kwargs)
        self.at_least_once = at_least_once
        self.eta = Real(eta, bounds=(3.0, 30.0), strict=(1.0, 100.0))
        self.dk = dk_name

    def _do(self, problem, X, params=None, **kwargs):
        X = X.astype(float)

        eta = get(self.eta, size=len(X))
        prob_var = self.get_prob_var(problem, size=len(X))

        Xp = modified_polynomial_mutation(X, problem.xl, problem.xu, eta,
                                          prob_var, problem.vars[self.dk],
                                          self.at_least_once)

        return Xp


class REFM(RenewableEnergyFavourMutation):
    pass


class ConventionalEnergyFavourMutation(Mutation):

    def __init__(self, prob=0.9, eta=20, dk_name="dk1", at_least_once=False,
                 **kwargs):
        """
        Parameters
        ----------
        - ``prob`` : float
            The probability of mutating a decision variable.

        - ``eta`` : float
            The mutation power.

        - ``dk_name`` : str
            The name of the column in the DataFrame that stores the domain
            knowledge.

        - ``at_least_once`` : bool
            Whether at least one decision variable should be mutated.

        - ``kwargs`` : dict
        """
        super().__init__(prob=prob, **kwargs)
        self.at_least_once = at_least_once
        self.eta = Real(eta, bounds=(3.0, 30.0), strict=(1.0, 100.0))
        self.dk = dk_name

    def _do(self, problem, X, params=None, **kwargs):
        X = X.astype(float)

        eta = get(self.eta, size=len(X))
        prob_var = self.get_prob_var(problem, size=len(X))

        Xp = modified_polynomial_mutation(X, problem.xl, problem.xu, eta,
                                          prob_var, problem.vars[self.dk],
                                          self.at_least_once)

        return Xp


class CEFM(ConventionalEnergyFavourMutation):
    pass


class DomainKnowledgeMutation(Mutation):

    def __init__(self, prob=0.9, eta=20, dk_names=["dk0", "dk1"],
                 at_least_once=False, **kwargs):
        """
        Parameters
        ----------
        - ``prob`` : float
            The probability of mutating a decision variable.

        - ``eta`` : float
            The mutation power.

        - ``dk_names`` : list(str)
            The name of the column in the DataFrame that stores the domain
            knowledge.

        - ``at_least_once`` : bool
            Whether at least one decision variable should be mutated.

        - ``kwargs`` : dict
        """
        super().__init__(prob=prob, **kwargs)
        self.at_least_once = at_least_once
        self.eta = Real(eta, bounds=(3.0, 30.0), strict=(1.0, 100.0))
        assert len(dk_names) == 2, "Two domain knowledge names are required."
        self.dk_names = dk_names

    def _do(self, problem, X, params=None, **kwargs):
        X = X.astype(float)

        eta = get(self.eta, size=len(X))
        prob_var = self.get_prob_var(problem, size=len(X))

        # Check that termination criterion is set to
        # MaximumGenerationTermination
        assert type(kwargs["algorithm"].termination).__name__ == \
            "MaximumGenerationTermination", \
            "The termination criterion must be MaximumGenerationTermination."

        # Modify the mutation probability
        prob_var = 1 - kwargs["algorithm"].n_gen / \
            kwargs["algorithm"].termination.n_max_gen

        # Create a three way split of the decision variables
        mask = np.random.choice([0, 1, 2], size=X.shape[0])

        # The first domain knowledge is used
        dk = self.dk_names[0]
        X0 = modified_polynomial_mutation(X[mask == 0], problem.xl, problem.xu,
                                          eta[mask == 0], prob_var[mask == 0],
                                          problem.vars[dk],
                                          self.at_least_once)

        # The second domain knowledge is used
        dk = self.dk_names[1]
        X1 = modified_polynomial_mutation(X[mask == 1], problem.xl, problem.xu,
                                          eta[mask == 1], prob_var[mask == 1],
                                          problem.vars[dk],
                                          self.at_least_once)

        # The rest of the decision variables undergo polynomial mutation
        X2 = mut_pm(X[mask == 2], problem.xl, problem.xu, eta[mask == 2],
                    prob_var[mask == 2], self.at_least_once)

        return np.concatenate([X0, X1, X2], axis=0)


class DKMutation(DomainKnowledgeMutation):
    pass


if __name__ == '__main__':
    pass
