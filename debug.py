from pymoo.optimize import minimize

from moea.models import get_model
from moea.algorithms import get_algorithm

# Load the model
model_name = "Oslo"
model = get_model(model_name)

# Load the algorithm
algorithm_name = "NSGAII"
algorithm = get_algorithm(algorithm_name, pop_size=10)

res = minimize(
    model,
    algorithm,
    ("n_gen", 10),
    seed=1,
    verbose=True
)

print(res.F)