import unittest

from pymoo.optimize import minimize

from moea.models import get_model
from moea.algorithms import get_algorithm


class TestAalborgA(unittest.TestCase):

    def setUp(self) -> None:
        self.model = get_model('AalborgA')
        self.algorithm = get_algorithm('NSGAII', pop_size=5)
        return super().setUp()

    def test_model_features(self):
        self.assertEqual(self.model.n_var, 7)
        self.assertEqual(self.model.n_obj, 2)
        self.assertEqual(self.model.n_ieq_constr, 3)

    def test_execution(self):
        res = minimize(
            problem=self.model,
            algorithm=self.algorithm,
            termination=('n_gen', 3),
            seed=1
        )
        self.assertIsNotNone(res.X)
        self.assertIsNotNone(res.F)
        # Check that at least one non-dominated solution is found
        self.assertGreaterEqual(res.F.shape[0], 1)


class TestAalborgB(unittest.TestCase):

    def setUp(self) -> None:
        self.model = get_model('AalborgB')
        self.algorithm = get_algorithm('NSGAII', pop_size=5)
        return super().setUp()

    def test_model_features(self):
        self.assertEqual(self.model.n_var, 7)
        self.assertEqual(self.model.n_obj, 2)
        self.assertEqual(self.model.n_ieq_constr, 3)

    def test_execution(self):
        res = minimize(
            problem=self.model,
            algorithm=self.algorithm,
            termination=('n_gen', 3),
            seed=1
        )
        self.assertIsNotNone(res.X)
        self.assertIsNotNone(res.F)
        # Check that at least one non-dominated solution is found
        self.assertGreaterEqual(res.F.shape[0], 1)


if __name__ == '__main__':
    unittest.main()
