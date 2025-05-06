import unittest

from pymoo.optimize import minimize

from moea.models import get_model
from moea.algorithms import get_algorithm


class TestAalborg(unittest.TestCase):

    def setUp(self) -> None:
        self.model = get_model('Aalborg')
        self.algorithm = get_algorithm('NSGAII', pop_size=10)
        return super().setUp()

    def test_model_features(self):
        self.assertEqual(self.model.n_var, 7)
        self.assertEqual(self.model.n_obj, 2)
        self.assertEqual(self.model.n_ieq_constr, 3)

    def test_execution(self):
        res = minimize(
            problem=self.model,
            algorithm=self.algorithm,
            termination=('n_gen', 10),
            seed=1
        )
        self.assertIsNotNone(res.X)
        self.assertIsNotNone(res.F)
        # Check that at least one non-dominated solution is found
        self.assertGreaterEqual(res.F.shape[0], 1)


class TestAalborgMahbub2016(unittest.TestCase):

    def setUp(self) -> None:
        self.model = get_model('Aalborg')
        self.algorithm = get_algorithm('mahbub2016', pop_size=5)
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


class TestGiudicarie(unittest.TestCase):

    def setUp(self) -> None:
        self.model = get_model('Giudicarie')
        self.algorithm = get_algorithm('NSGAII', pop_size=50)
        return super().setUp()

    def test_model_features(self):
        self.assertEqual(self.model.n_var, 6)
        self.assertEqual(self.model.n_obj, 4)
        self.assertEqual(self.model.n_ieq_constr, 1)

    def test_execution(self):
        res = minimize(
            problem=self.model,
            algorithm=self.algorithm,
            termination=('n_gen', 5),
            seed=987
        )
        self.assertIsNotNone(res.X)
        self.assertIsNotNone(res.F)
        # Check that at least one non-dominated solution is found
        self.assertGreaterEqual(res.F.shape[0], 1)


class TestValDiNon(unittest.TestCase):

    def setUp(self) -> None:
        self.model = get_model('vdn', year=2020)
        self.algorithm = get_algorithm('NSGAII', pop_size=5)
        return super().setUp()

    def test_model_features(self):
        self.assertEqual(self.model.n_var, 11)
        self.assertEqual(self.model.n_obj, 2)
        self.assertEqual(self.model.n_ieq_constr, 1)

    def test_execution(self):
        res = minimize(
            problem=self.model,
            algorithm=self.algorithm,
            termination=('n_gen', 5),
            seed=987
        )
        self.assertIsNotNone(res.X)
        self.assertIsNotNone(res.F)
        # Check that at least one non-dominated solution is found
        self.assertGreaterEqual(res.F.shape[0], 1)


if __name__ == '__main__':
    unittest.main()
