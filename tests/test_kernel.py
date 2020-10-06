# -*- coding: utf-8 -*-
# test kernels

import numpy as np                                                # type: ignore
import unittest
from math import exp, sqrt, pi, sin
from scipy.optimize import check_grad, approx_fprime              # type: ignore
from gpie.base import Bounds
from gpie.kernel import ConstantKernel, WhiteKernel, RBFKernel, \
    RationalQuadraticKernel, MaternKernel, PeriodicKernel, SpectralKernel, \
    LinearKernel, NeuralKernel, GaussianProcessRegressor, BayesianOptimizer


def beale(x1_x2) -> float:
    """
    smooth with edges sticking up
    f_min = 0.
    x_min = (3.0, 0.5)
    """
    x1, x2 = x1_x2[0], x1_x2[1]
    return (1.5 - x1 + x1 * x2) ** 2 +\
           (2.25 - x1 + x1 * x2**2) ** 2 +\
           (2.625 - x1 + x1 * x2**3) ** 2


class KernelTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.X = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)
        cls.Z = np.array([[1, 0, 0], [1, 1, 0], [1, 1, 1]], dtype=float)
        cls.y = np.array([0.9, 0.5, 0.2])
        # cls.U = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)
        # cls.V = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)
        # cls.w = np.array([0.9, 0.5, 0.2])  # FIXME add randomized test points

    def _check_grad(self, fun, jac, x):
        ag = jac(x)
        ng = approx_fprime(x, fun, 1e-8)
        err = np.abs(ag - ng).max()
        if not err < 1e-4:
            print('\nanalytical gradient {}'.format(ag))
            print('numerical  gradient {}\n'.format(ng))
            self.assertTrue(err < 1e-4)

    def test_constant(self):
        const = ConstantKernel(1.)
        white = WhiteKernel()
        res = np.ones((3, 3))
        self.assertTrue(np.allclose(const(self.X, self.X), res))
        self.assertTrue(np.allclose(const(self.X, self.Z), res))
        # jacobian
        # constant kernel cannot be tested alone due to its singularity
        gpr = GaussianProcessRegressor(kernel=const * white)
        f = gpr._obj(self.X, self.y)
        fun = lambda x: f(x)[0]
        jac = lambda x: f(x)[1]
        for p in (np.ones((len(gpr.thetas),)), gpr.thetas.values,
                  np.random.uniform(0., 1., (len(gpr.thetas),))):
            self._check_grad(fun, jac, p)

    def test_white(self):
        white = WhiteKernel()
        res = np.eye(3)
        self.assertTrue(np.allclose(white(self.X, self.X), res))
        res = np.zeros((3, 3))
        res[0, 0] += 1.
        self.assertTrue(np.allclose(white(self.X, self.Z), res))
        # jacobian
        gpr = GaussianProcessRegressor(kernel=white)
        f = gpr._obj(self.X, self.y)
        fun = lambda x: f(x)[0]
        jac = lambda x: f(x)[1]
        for p in (np.ones((len(gpr.thetas),)), gpr.thetas.values,
                  np.random.uniform(0., 1., (len(gpr.thetas),))):
            self.assertTrue(jac(p).shape == (0,))  # no learnable parameter

    def test_rbf_iso(self):
        rbf = RBFKernel(1.)
        res = np.ones((3, 3)) * exp(-1)
        res[np.diag_indices_from(res)] = 1.
        self.assertTrue(np.allclose(rbf(self.X, self.X), res))
        # jacobian
        gpr = GaussianProcessRegressor(kernel=rbf)
        f = gpr._obj(self.X, self.y)
        fun = lambda x: f(x)[0]
        jac = lambda x: f(x)[1]
        for p in (np.ones((len(gpr.thetas),)), gpr.thetas.values,
                  np.random.uniform(0., 1., (len(gpr.thetas),))):
            self._check_grad(fun, jac, p)

    def test_rbf_ard(self):
        rbf = RBFKernel(np.ones((3,)),
                        l_bounds=(np.ones((3,))*1e-5, np.ones((3,))*1e5))
        res = np.ones((3, 3)) * exp(-1)
        res[np.diag_indices_from(res)] = 1.
        self.assertTrue(np.allclose(rbf(self.X, self.X), res))
        # jacobian
        gpr = GaussianProcessRegressor(kernel=rbf)
        f = gpr._obj(self.X, self.y)
        fun = lambda x: f(x)[0]
        jac = lambda x: f(x)[1]
        for p in (np.ones((len(gpr.thetas),)), gpr.thetas.values,
                  np.random.uniform(0., 1., (len(gpr.thetas),))):
            self._check_grad(fun, jac, p)

    def test_rational_quadratic_iso(self):
        rq = RationalQuadraticKernel(1., 1.)
        res = np.ones((3, 3)) * 0.5
        res[np.diag_indices_from(res)] = 1.
        self.assertTrue(np.allclose(rq(self.X, self.X), res))
        # jacobian
        gpr = GaussianProcessRegressor(kernel=rq)
        f = gpr._obj(self.X, self.y)
        fun = lambda x: f(x)[0]
        jac = lambda x: f(x)[1]
        for p in (np.ones((len(gpr.thetas),)), gpr.thetas.values,
                  np.random.uniform(0., 1., (len(gpr.thetas),))):
            self._check_grad(fun, jac, p)

    def test_rational_quadratic_ard(self):
        rq = RationalQuadraticKernel(1., np.ones((3,)),
                l_bounds=(np.ones((3,))*1e-5, np.ones((3,))*1e5))
        res = np.ones((3, 3)) * 0.5
        res[np.diag_indices_from(res)] = 1.
        self.assertTrue(np.allclose(rq(self.X, self.X), res))
        # jacobian
        gpr = GaussianProcessRegressor(kernel=rq)
        f = gpr._obj(self.X, self.y)
        fun = lambda x: f(x)[0]
        jac = lambda x: f(x)[1]
        for p in (np.ones((len(gpr.thetas),)), gpr.thetas.values,
                  np.random.uniform(0., 1., (len(gpr.thetas),))):
            self._check_grad(fun, jac, p)

    def test_matern_iso(self):
        # d = 1
        matern1 = MaternKernel(1, 1.)
        res = np.ones((3, 3)) * -sqrt(2.)
        res[np.diag_indices_from(res)] = 0.
        res = np.exp(res)
        self.assertTrue(np.allclose(matern1(self.X, self.X), res))
        # d = 3
        matern3 = MaternKernel(3, 1.)
        res = np.ones((3, 3)) * sqrt(6.)
        res[np.diag_indices_from(res)] = 0.
        res += 1.
        tmp = np.ones((3, 3)) * -sqrt(6.)
        tmp[np.diag_indices_from(tmp)] = 0.
        tmp = np.exp(tmp)
        res *= tmp
        self.assertTrue(np.allclose(matern3(self.X, self.X), res))
        # d = 5
        matern5 = MaternKernel(5, 1.)
        res = np.ones((3, 3)) * sqrt(10.)
        res[np.diag_indices_from(res)] = 0.
        res = 1./3. * res**2 + res + 1.
        tmp = np.ones((3, 3)) * -sqrt(10.)
        tmp[np.diag_indices_from(tmp)] = 0.
        tmp = np.exp(tmp)
        res *= tmp
        self.assertTrue(np.allclose(matern5(self.X, self.X), res))
        # jacobian
        for matern in (matern1, matern3, matern5):
            gpr = GaussianProcessRegressor(kernel=matern)
            f = gpr._obj(self.X, self.y)
            fun = lambda x: f(x)[0]
            jac = lambda x: f(x)[1]
            for p in (np.ones((len(gpr.thetas),)), gpr.thetas.values,
                      np.random.uniform(0., 1., (len(gpr.thetas),))):
                self._check_grad(fun, jac, p)

    def test_matern_ard(self):
        # d = 1
        matern1 = MaternKernel(1, np.ones((3,)),
                              l_bounds=(np.ones((3,))*1e-5, np.ones((3,))*1e5))
        res = np.ones((3, 3)) * -sqrt(2.)
        res[np.diag_indices_from(res)] = 0.
        res = np.exp(res)
        self.assertTrue(np.allclose(matern1(self.X, self.X), res))
        # d = 3
        matern3 = MaternKernel(3, np.ones((3,)),
                              l_bounds=(np.ones((3,))*1e-5, np.ones((3,))*1e5))
        res = np.ones((3, 3)) * sqrt(6.)
        res[np.diag_indices_from(res)] = 0.
        res += 1.
        tmp = np.ones((3, 3)) * -sqrt(6.)
        tmp[np.diag_indices_from(tmp)] = 0.
        tmp = np.exp(tmp)
        res *= tmp
        self.assertTrue(np.allclose(matern3(self.X, self.X), res))
        # d = 5
        matern5 = MaternKernel(5, np.ones((3,)),
                              l_bounds=(np.ones((3,))*1e-5, np.ones((3,))*1e5))
        res = np.ones((3, 3)) * sqrt(10.)
        res[np.diag_indices_from(res)] = 0.
        res = 1./3. * res**2 + res + 1.
        tmp = np.ones((3, 3)) * -sqrt(10.)
        tmp[np.diag_indices_from(tmp)] = 0.
        tmp = np.exp(tmp)
        res *= tmp
        self.assertTrue(np.allclose(matern5(self.X, self.X), res))
        # jacobian
        for matern in (matern1, matern3, matern5):
            gpr = GaussianProcessRegressor(kernel=matern)
            f = gpr._obj(self.X, self.y)
            fun = lambda x: f(x)[0]
            jac = lambda x: f(x)[1]
            for p in (np.ones((len(gpr.thetas),)), gpr.thetas.values,
                      np.random.uniform(0., 1., (len(gpr.thetas),))):
                self._check_grad(fun, jac, p)

    def test_periodic_iso(self):
        periodic = PeriodicKernel(1., 1.)
        res = np.ones((3, 3)) * exp(-4. * sin(1.)**2)
        res[np.diag_indices_from(res)] = 1.
        self.assertTrue(np.allclose(periodic(self.X, self.X), res))
        # jacobian
        gpr = GaussianProcessRegressor(kernel=periodic)
        f = gpr._obj(self.X, self.y)
        fun = lambda x: f(x)[0]
        jac = lambda x: f(x)[1]
        for p in (np.ones((len(gpr.thetas),)), gpr.thetas.values,
                  np.random.uniform(0., 1., (len(gpr.thetas),))):
            self._check_grad(fun, jac, p)

    def test_periodic_ard(self):
        periodic = PeriodicKernel(np.ones((3,)), np.ones((3,)),
                       p_bounds=(np.ones((3,))*1e-5, np.ones((3,))*1e5),
                       l_bounds=(np.ones((3,))*1e-5, np.ones((3,))*1e5))
        res = np.ones((3, 3)) * exp(-4. * sin(1.)**2)
        res[np.diag_indices_from(res)] = 1.
        self.assertTrue(np.allclose(periodic(self.X, self.X), res))
        # jacobian
        gpr = GaussianProcessRegressor(kernel=periodic)
        f = gpr._obj(self.X, self.y)
        fun = lambda x: f(x)[0]
        jac = lambda x: f(x)[1]
        for p in (np.ones((len(gpr.thetas),)), gpr.thetas.values,
                  np.random.uniform(0., 1., (len(gpr.thetas),))):
            self._check_grad(fun, jac, p)

    def test_spectral_iso(self):
        rbf = RBFKernel(1.)
        spectral = SpectralKernel(1., 1.)
        self.assertTrue(np.allclose(rbf(self.X, self.X),
                                    spectral(self.X, self.X)))
        angle = np.zeros((3, 3))
        angle[:, 1] = -1.
        angle[:, 2] = -2.
        self.assertTrue(np.allclose(rbf(self.X, self.Z) * np.cos(angle),
                                    spectral(self.X, self.Z)))
        # jacobian
        gpr = GaussianProcessRegressor(kernel=spectral)
        f = gpr._obj(self.X, self.y)
        fun = lambda x: f(x)[0]
        jac = lambda x: f(x)[1]
        for p in (np.ones((len(gpr.thetas),)), gpr.thetas.values,
                  np.random.uniform(0., 1., (len(gpr.thetas),))):
            self._check_grad(fun, jac, p)

    def test_spectral_ard(self):
        rbf = RBFKernel(1.)
        spectral = SpectralKernel(np.ones((3,)), np.ones((3,)),
                       p_bounds=(np.ones((3,))*1e-5, np.ones((3,))*1e5),
                       l_bounds=(np.ones((3,))*1e-5, np.ones((3,))*1e5))
        self.assertTrue(np.allclose(rbf(self.X, self.X),
                                    spectral(self.X, self.X)))
        angle = np.zeros((3, 3))
        angle[:, 1] = -1.
        angle[:, 2] = -2.
        self.assertTrue(np.allclose(rbf(self.X, self.Z) * np.cos(angle),
                                    spectral(self.X, self.Z)))
        # jacobian
        gpr = GaussianProcessRegressor(kernel=spectral)
        f = gpr._obj(self.X, self.y)
        fun = lambda x: f(x)[0]
        jac = lambda x: f(x)[1]
        for p in (np.ones((len(gpr.thetas),)), gpr.thetas.values,
                  np.random.uniform(0., 1., (len(gpr.thetas),))):
            self._check_grad(fun, jac, p)

    def test_linear_iso(self):
        linear = LinearKernel(1.)
        self.assertTrue(np.allclose(linear(self.X, self.X), self.X))
        # jacobian
        gpr = GaussianProcessRegressor(kernel=linear)
        f = gpr._obj(self.X, self.y)
        fun = lambda x: f(x)[0]
        jac = lambda x: f(x)[1]
        for p in (np.ones((len(gpr.thetas),)), gpr.thetas.values,
                  np.random.uniform(0., 1., (len(gpr.thetas),))):
            self._check_grad(fun, jac, p)

    def test_linear_ard(self):
        linear = LinearKernel(np.ones((3,)),
                              l_bounds=(np.ones((3,))*1e-5, np.ones((3,))*1e5))
        self.assertTrue(np.allclose(linear(self.X, self.X), self.X))
        res = np.array([[1, 1, 1], [1, 2, 2], [1, 2, 3]], dtype=float)
        self.assertTrue(np.allclose(linear(self.Z, self.Z), res))
        # jacobian
        gpr = GaussianProcessRegressor(kernel=linear)
        f = gpr._obj(self.X, self.y)
        fun = lambda x: f(x)[0]
        jac = lambda x: f(x)[1]
        for p in (np.ones((len(gpr.thetas),)), gpr.thetas.values,
                  np.random.uniform(0., 1., (len(gpr.thetas),))):
            self._check_grad(fun, jac, p)

    def test_neural_iso(self):
        neural = NeuralKernel(1., 1.)
        res = 2./pi * np.arcsin((np.ones((3, 3)) + np.eye(3)) / 3.)
        self.assertTrue(np.allclose(neural(self.X, self.X), res))
        # jacobian
        gpr = GaussianProcessRegressor(kernel=neural)
        f = gpr._obj(self.X, self.y)
        fun = lambda x: f(x)[0]
        jac = lambda x: f(x)[1]
        for p in (np.ones((len(gpr.thetas),)), gpr.thetas.values,
                  np.random.uniform(0., 1., (len(gpr.thetas),))):
            self._check_grad(fun, jac, p)

    def test_neural_ard(self):
        neural = NeuralKernel(1., np.ones((3,)),
                              l_bounds=(np.ones((3,))*1e-5, np.ones((3,))*1e5))
        res = 2./pi * np.arcsin((np.ones((3, 3)) + np.eye(3)) / 3.)
        self.assertTrue(np.allclose(neural(self.X, self.X), res))
        # jacobian
        gpr = GaussianProcessRegressor(kernel=neural)
        f = gpr._obj(self.X, self.y)
        fun = lambda x: f(x)[0]
        jac = lambda x: f(x)[1]
        for p in (np.ones((len(gpr.thetas),)), gpr.thetas.values,
                  np.random.uniform(0., 1., (len(gpr.thetas),))):
            self._check_grad(fun, jac, p)

    def test_sum(self):
        ker = RBFKernel(1.) + WhiteKernel()
        res = np.ones((3, 3)) * exp(-1)
        res[np.diag_indices_from(res)] = 2.
        self.assertTrue(np.allclose(ker(self.X, self.X), res))

    def test_prod(self):
        ker = RBFKernel(1.) * WhiteKernel()
        res = np.eye(3)
        self.assertTrue(np.allclose(ker(self.X, self.X), res))

    def test_exp(self):
        rbf = RBFKernel(1.) ** 2
        res = np.ones((3, 3)) * exp(-1)
        res[np.diag_indices_from(res)] = 1.
        res **= 2
        self.assertTrue(np.allclose(rbf(self.X, self.X), res))

    # def test_kronecker_sum(self):
    #     pass

    # def test_kronecker_prod(self):
    #     pass

    def test_gpr(self):
        k = self.X.shape[1]
        ker = RBFKernel(l=np.ones((k,)),
                        l_bounds=(np.ones((k,))*1e-4, np.ones((k,))*1e4)) + \
              RationalQuadraticKernel() + \
              WhiteKernel()
        gpr = GaussianProcessRegressor(kernel=ker)
        # gradient
        f = gpr._obj(self.X, self.y)
        fun = lambda x: f(x)[0]
        jac = lambda x: f(x)[1]
        for p in (gpr.thetas.values, np.ones((len(gpr.thetas),))):
            ag = jac(p)
            ng = approx_fprime(p, fun, 1e-8)
            err = np.abs(ag - ng).max()
            try:
                assert err < 1e-6
            except AssertionError:
                print('analytical gradient {}'.format(ag))
                print('numerical  gradient {}'.format(ng))
                self.fail('gpr gradient fails.')
        # fitted
        self.assertFalse(gpr.fitted())
        # fit
        try:
            gpr.fit(self.X, self.y)
        except Exception:
            self.fail('gpr fit fails.')
        # precompute
        err = np.abs(gpr.kernel(self.X, self.X) - gpr.L @ gpr.L.T).max()
        self.assertTrue(err < 1e-6)
        # point prediction
        try:
            gpr.predict(self.Z)
        except Exception:
            self.fail('gpr predict fails.')
        # distributive prediction
        try:
            gpr.predict_prob(self.Z)
        except Exception:
            self.fail('gpr predict prob fails.')

    # def test_tpr(self):
    #     pass

    # def test_gpc(self):
    #     pass

    # def test_tpc(self):
    #     pass

    # # def test_bo(self):
    # #     b = Bounds(np.array([-4., -4.]), np.array([4., 4.]))
    # #     x = np.random.uniform(0., 3.5, (10, 2))
    # #     try:
    # #         bo = BayesianOptimizer(fun=beale, bounds=b, x0=x, acquisition='ei')
    # #         print(bo.minimize())
    # #     except Exception:
    # #         self.fail('bayesian optimizer fails.')

    # def test_svr(self):
    #     pass

    # def test_svc(self):
    #     pass


if __name__ == '__main__':
    unittest.main()