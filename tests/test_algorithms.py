import unittest
import numpy as np

from pymoo.optimize import minimize

from moea.models import get_model
from moea.algorithms import get_algorithm
from moea.algorithms.base_algorithm import BaseAlgorithm


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
        self.algorithm = get_algorithm('NSGAII', pop_size=5)
        return super().setUp()

    def test_model_features(self):
        self.assertEqual(self.model.n_var, 6)
        self.assertEqual(self.model.n_obj, 4)
        self.assertEqual(self.model.n_ieq_constr, 1)

    def test_model(self):
        X = np.array([
            [26965.63379369457, 0.004340334553761934, 0.020919167336427853, 0.37303784725602784, 0.7972038525947666, 0.9731818827459553],
            [5028.4140851378215, 0.010382724450131785, 0.025554225786505076, 0.3507161626172153, 0.7400955952948144, 0.16779536815296964],
            [18330.112744068123 ,0.770837235292494E-4, 0.03415166975730164, 0.27333832832593663, 0.7435772304082318, 0.7821214577447164],
            [32117.357695599305, 0.008219071431419537, 0.010247094202882986, 0.025055677414418283, 0.7512839092204443, 0.06605223833219542],
            [29591.875618786427, 0.006303746797726764, 0.06485647859171757, 0.578730409048231, 0.7914934027733642, 0.17419317044036814],
        ])

        algorithm = BaseAlgorithm(
            pop_size=X.shape[0],
            sampling=X
        )
        res = minimize(
            problem=self.model,
            algorithm=algorithm,
            termination=("n_gen", 1),
            seed=1
        )


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
