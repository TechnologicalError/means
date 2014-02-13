import unittest
from means.approximation.ode_problem import Moment
import sympy

from means.approximation.mea.log_normal_closer import LogNormalCloser
from means.util.sympyhelpers import sympy_expressions_equal
from means.util.sympyhelpers import to_sympy_matrix

class TestLogNormalCloser(unittest.TestCase):

    __problem_moments = [
            Moment([1, 0, 0], symbol=sympy.Symbol("y_0")),
            Moment([0, 1, 0], symbol=sympy.Symbol("y_1")),
            Moment([0, 0, 1], symbol=sympy.Symbol("y_2")),
            Moment([0, 0, 2], symbol=sympy.Symbol("yx2")),
            Moment([0, 1, 1], symbol=sympy.Symbol("yx3")),
            Moment([0, 2, 0], symbol=sympy.Symbol("yx4")),
            Moment([1, 0, 1], symbol=sympy.Symbol("yx5")),
            Moment([1, 1, 0], symbol=sympy.Symbol("yx6")),
            Moment([2, 0, 0], symbol=sympy.Symbol("yx7")),
            Moment([0, 0, 3], symbol=sympy.Symbol("yx8")),
            Moment([0, 1, 2], symbol=sympy.Symbol("yx9")),
            Moment([0, 2, 1], symbol=sympy.Symbol("yx10")),
            Moment([0, 3, 0], symbol=sympy.Symbol("yx11")),
            Moment([1, 0, 2], symbol=sympy.Symbol("yx12")),
            Moment([1, 1, 1], symbol=sympy.Symbol("yx13")),
            Moment([1, 2, 0], symbol=sympy.Symbol("yx14")),
            Moment([2, 0, 1], symbol=sympy.Symbol("yx15")),
            Moment([2, 1, 0], symbol=sympy.Symbol("yx16")),
            Moment([3, 0, 0], symbol=sympy.Symbol("yx17"))
        ]
    def test_get_log_covariance(self):


        log_variance_mat =to_sympy_matrix([
                ["log(1+yx7/y_0**2)", "0", "0"],
                ["0", "log(1+yx4/y_1**2)", "0"],
                ["0", "0", "log(1+yx2/y_2**2)"]
                        ])

        log_expectation_symbols = to_sympy_matrix([
                ["log(y_0)-log(1+yx7/y_0**2)/2"],
                ["log(y_1)-log(1+yx4/y_1**2)/2"],
                ["log(y_2)-log(1+yx2/y_2**2)/2"]
                ])

        covariance_matrix = to_sympy_matrix([
                ["yx7","yx6","yx5"],
                ["yx6","yx4","yx3"],
                ["yx5","yx3","yx2"]])

        expected = sympy.sympify("log(1 + yx6/(y_0*y_1))")


        closer = LogNormalCloser(3,multivariate=True)
        answer = closer.get_log_covariance(log_variance_mat, log_expectation_symbols, covariance_matrix, 0,1)

        self.assertEqual(answer, expected)

        answer1 = closer.get_log_covariance(log_variance_mat, log_expectation_symbols, covariance_matrix, 1,2)
        answer2 = closer.get_log_covariance(log_variance_mat, log_expectation_symbols, covariance_matrix, 1,2)
        #logcovariance between species 1 and 2  ==  covarianc between sp. 2 and 1
        self.assertEqual(answer1, answer2)

    def test_get_covariance_symbol(self):
        closer = LogNormalCloser(3,multivariate=True)
        problem_moments = self.__problem_moments
        expected = sympy.Symbol("yx3")
        answer = closer.get_covariance_symbol(problem_moments,1, 2)
        self.assertEqual(answer, expected)

    def test_get_covariance_symbol2(self):
        closer = LogNormalCloser(3,multivariate=True)
        problem_moments = self.__problem_moments
        expected = sympy.Symbol("yx6")
        answer = closer.get_covariance_symbol(problem_moments,1, 0)
        self.assertEqual(answer, expected)

    def test_get_covariance_symbol_is_triangular(self):
        closer = LogNormalCloser(3,multivariate=True)
        problem_moments = self.__problem_moments
        #covariance between species 1 and 2  ==  covariance between sp. 2 and 1
        answer1 =closer.get_covariance_symbol(problem_moments,1, 0)
        answer2 = closer.get_covariance_symbol(problem_moments,0, 1)
        self.assertEqual(answer1, answer2)


    def test_compute_raw_moments(self):

        n_species = 3
        problem_moments = self.__problem_moments

        expected = to_sympy_matrix([
            ["y_2**2+yx2"],
            ["y_1*y_2+yx3"],
            ["y_1**2+yx4"],
            ["y_0*y_2+yx5"],
            ["y_0*y_1+yx6"],
            ["y_0**2+yx7"],
            ["y_2**3+3*y_2*yx2+3*yx2**2/y_2+yx2**3/y_2**3"],
            ["y_1*y_2**2+y_1*yx2+2*y_2*yx3+2*yx2*yx3/y_2+yx3**2/y_1+yx2*yx3**2/(y_1*y_2**2)"],
            ["y_1**2*y_2+2*y_1*yx3+y_2*yx4+yx3**2/y_2+2*yx3*yx4/y_1+yx3**2*yx4/(y_1**2*y_2)"],
            ["y_1**3+3*y_1*yx4+3*yx4**2/y_1+yx4**3/y_1**3"],
            ["y_0*y_2**2+y_0*yx2+2*y_2*yx5+2*yx2*yx5/y_2+yx5**2/y_0+yx2*yx5**2/(y_0*y_2**2)"],
            ["y_0*y_1*y_2+y_0*yx3+y_1*yx5+y_2*yx6+yx3*yx5/y_2+yx3*yx6/y_1+yx5*yx6/y_0+yx3*yx5*yx6/(y_0*y_1*y_2)"],
            ["y_0*y_1**2+y_0*yx4+2*y_1*yx6+2*yx4*yx6/y_1+yx6**2/y_0+yx4*yx6**2/(y_0*y_1**2)"],
            ["y_0**2*y_2+2*y_0*yx5+y_2*yx7+yx5**2/y_2+2*yx5*yx7/y_0+yx5**2*yx7/(y_0**2*y_2)"],
            ["y_0**2*y_1+2*y_0*yx6+y_1*yx7+yx6**2/y_1+2*yx6*yx7/y_0+yx6**2*yx7/(y_0**2*y_1)"],
            ["y_0**3+3*y_0*yx7+3*yx7**2/y_0+yx7**3/y_0**3"]
        ])
        closer = LogNormalCloser(3,multivariate=True)
        answer = closer.compute_raw_moments(n_species,problem_moments)

        self.assertEqual(answer, expected)

    def test_log_normal_closer_wrapper(self):

        mfk = to_sympy_matrix([
                    ["-(c_2*c_6*y_2*yx17*(c_6+y_0)**6+c_2*c_6*yx5*(c_6+y_0)**8+c_2*y_0*y_2*(c_6+y_0)**9-(c_0-c_1*y_0)*(c_6+y_0)**10-(c_6+y_0)**7*(c_2*c_6*y_2*yx7+c_2*c_6*yx15))/(c_6+y_0)**10"],
                    ["c_3*y_0-c_4*y_1"],
                    ["c_4*y_1-c_5*y_2"],
                    ["c_4*y_1+2*c_4*yx3+c_5*y_2-2*c_5*yx2"],
                    ["c_3*yx5-c_4*y_1+c_4*yx4-yx3*(c_4+c_5)"],
                    ["c_3*y_0+2*c_3*yx6+c_4*y_1-2*c_4*yx4"],
                    ["c_2*c_6*y_2*yx15/(c_6**3+3*c_6**2*y_0+3*c_6*y_0**2+y_0**3)-c_2*y_0*yx2/(c_6+y_0)+c_2*yx12*(y_0/(c_6+y_0)-1)/(c_6+y_0)+c_4*yx6-yx5*(-c_2*c_6*y_2-2*c_2*y_0*y_2+2*c_2*y_2*(c_6+y_0)+(c_1+c_5)*(c_6+y_0)**2)/(c_6+y_0)**2"],
                    ["-(c_2*c_6*yx13*(c_6+y_0)**4+c_2*y_0*yx3*(c_6+y_0)**5-c_3*yx7*(c_6+y_0)**6-(c_6+y_0)**3*(c_2*c_6*y_2*yx16-yx6*(-c_2*y_0*y_2*(c_6+y_0)+c_2*y_2*(c_6+y_0)**2+(c_1+c_4)*(c_6+y_0)**3)))/(c_6+y_0)**6"],
                    ["c_2*c_6*y_2*yx17*(2*c_6+2*y_0+1)/(c_6**4+4*c_6**3*y_0+6*c_6**2*y_0**2+4*c_6*y_0**3+y_0**4)-c_2*c_6*yx15*(-2*c_6-2*y_0-1)/(-c_6**3-3*c_6**2*y_0-3*c_6*y_0**2-y_0**3)+c_2*yx5*(-2*c_6*y_0+c_6-2*y_0**2)/(c_6**2+2*c_6*y_0+y_0**2)+yx7*(2*c_1*c_6**3+6*c_1*c_6**2*y_0+6*c_1*c_6*y_0**2+2*c_1*y_0**3+2*c_2*c_6**2*y_2+2*c_2*c_6*y_0*y_2+c_2*c_6*y_2)/(-c_6**3-3*c_6**2*y_0-3*c_6*y_0**2-y_0**3)+(c_0*c_6+c_0*y_0+c_1*c_6*y_0+c_1*y_0**2+c_2*y_0*y_2)/(c_6+y_0)"],
                    ["c_4*y_1+3*c_4*yx3+3*c_4*yx9-c_5*y_2+3*c_5*yx2-3*c_5*yx8"],
                    ["c_3*yx12-c_4*y_1+2*c_4*yx10-2*c_4*yx3+c_4*yx4-c_4*yx9+c_5*yx3-2*c_5*yx9"],
                    ["2*c_3*yx13+c_3*yx5+c_4*y_1-2*c_4*yx10+c_4*yx11+c_4*yx3-2*c_4*yx4-c_5*yx10"],
                    ["c_3*y_0+3*c_3*yx14+3*c_3*yx6-c_4*y_1-3*c_4*yx11+3*c_4*yx4"],
                    ["c_2*c_6*y_2*yx17*yx2/(c_6**4+4*c_6**3*y_0+6*c_6**2*y_0**2+4*c_6*y_0**3+y_0**4)-c_2*c_6*y_2*yx2*yx7/(c_6**3+3*c_6**2*y_0+3*c_6*y_0**2+y_0**3)-c_2*c_6*yx15*yx2/(c_6**3+3*c_6**2*y_0+3*c_6*y_0**2+y_0**3)-c_2*y_0*yx8/(c_6+y_0)+2*c_4*yx13+c_4*yx6-yx12*(-2*c_2*c_6*y_2-3*c_2*y_0*y_2+3*c_2*y_2*(c_6+y_0)+(c_1+2*c_5)*(c_6+y_0)**2)/(c_6+y_0)**2-yx2*(c_2*y_0*y_2-(c_0-c_1*y_0)*(c_6+y_0))/(c_6+y_0)+yx5*(c_2*c_6*yx2+2*c_4*c_6**2*y_1+4*c_4*c_6*y_0*y_1+2*c_4*y_0**2*y_1-2*c_5*c_6**2*y_2+c_5*c_6**2-4*c_5*c_6*y_0*y_2+2*c_5*c_6*y_0-2*c_5*y_0**2*y_2+c_5*y_0**2)/(c_6**2+2*c_6*y_0+y_0**2)+(-c_0*c_6*yx2-c_0*y_0*yx2+c_1*c_6*y_0*yx2+c_1*y_0**2*yx2+c_2*y_0*y_2*yx2-2*c_4*c_6*y_1*yx5-2*c_4*y_0*y_1*yx5+2*c_5*c_6*y_2*yx5+2*c_5*y_0*y_2*yx5)/(c_6+y_0)"],
                    ["c_2*c_6*y_2*yx17*yx3/(c_6**4+4*c_6**3*y_0+6*c_6**2*y_0**2+4*c_6*y_0**3+y_0**4)-c_2*c_6*y_2*yx3*yx7/(c_6**3+3*c_6**2*y_0+3*c_6*y_0**2+y_0**3)-c_2*y_0*yx9/(c_6+y_0)+c_4*yx14-yx13*(-c_2*c_6*y_2-2*c_2*y_0*y_2+2*c_2*y_2*(c_6+y_0)+(c_6+y_0)**2*(c_1+c_4+c_5))/(c_6+y_0)**2+yx15*(-c_2*c_6*yx3+c_3*c_6**3+3*c_3*c_6**2*y_0+3*c_3*c_6*y_0**2+c_3*y_0**3)/(c_6**3+3*c_6**2*y_0+3*c_6*y_0**2+y_0**3)-yx3*(-c_0*c_6-c_0*y_0+c_1*c_6*y_0+c_1*y_0**2+c_2*y_0*y_2)/(c_6+y_0)+yx5*(c_2*c_6*yx3+c_3*c_6**2*y_0+2*c_3*c_6*y_0**2+c_3*y_0**3-c_4*c_6**2*y_1-2*c_4*c_6*y_0*y_1-c_4*y_0**2*y_1)/(c_6**2+2*c_6*y_0+y_0**2)-yx6*(-c_4*y_1+c_4+c_5*y_2)+(-c_0*c_6*yx3-c_0*y_0*yx3+c_1*c_6*y_0*yx3+c_1*y_0**2*yx3+c_2*y_0*y_2*yx3-c_3*c_6*y_0*yx5-c_3*y_0**2*yx5+c_4*c_6*y_1*yx5-c_4*c_6*y_1*yx6+c_4*y_0*y_1*yx5-c_4*y_0*y_1*yx6+c_5*c_6*y_2*yx6+c_5*y_0*y_2*yx6)/(c_6+y_0)"],
                    ["c_2*c_6*y_2*yx17*yx4/(c_6**4+4*c_6**3*y_0+6*c_6**2*y_0**2+4*c_6*y_0**3+y_0**4)-c_2*c_6*yx15*yx4/(c_6**3+3*c_6**2*y_0+3*c_6*y_0**2+y_0**3)+c_2*c_6*yx4*yx5/(c_6**2+2*c_6*y_0+y_0**2)-c_2*y_0*yx10/(c_6+y_0)+2*c_3*yx16-yx14*(-c_2*y_0*y_2+c_2*y_2*(c_6+y_0)+(c_1+2*c_4)*(c_6+y_0)**2)/(c_6+y_0)**2-yx4*(c_2*y_0*y_2-(c_0-c_1*y_0)*(c_6+y_0))/(c_6+y_0)+yx6*(2*c_3*y_0-2*c_4*y_1+c_4)+yx7*(-c_2*c_6*y_2*yx4+c_3*c_6**3+3*c_3*c_6**2*y_0+3*c_3*c_6*y_0**2+c_3*y_0**3)/(c_6**3+3*c_6**2*y_0+3*c_6*y_0**2+y_0**3)+(-c_0*c_6*yx4-c_0*y_0*yx4+c_1*c_6*y_0*yx4+c_1*y_0**2*yx4+c_2*y_0*y_2*yx4-2*c_3*c_6*y_0*yx6-2*c_3*y_0**2*yx6+2*c_4*c_6*y_1*yx6+2*c_4*y_0*y_1*yx6)/(c_6+y_0)"],
                    ["2*c_2*c_6*y_2*yx17*yx5/(c_6**4+4*c_6**3*y_0+6*c_6**2*y_0**2+4*c_6*y_0**3+y_0**4)+c_2*y_0*yx2/(c_6+y_0)-c_2*yx12*(2*c_6*y_0-c_6+2*y_0**2)/(c_6**2+2*c_6*y_0+y_0**2)+c_4*yx16-yx15*(2*c_1*c_6**3+6*c_1*c_6**2*y_0+6*c_1*c_6*y_0**2+2*c_1*y_0**3+2*c_2*c_6**2*y_2+2*c_2*c_6*y_0*y_2+c_2*c_6*y_2+2*c_2*c_6*yx5+c_5*c_6**3+3*c_5*c_6**2*y_0+3*c_5*c_6*y_0**2+c_5*y_0**3)/(c_6**3+3*c_6**2*y_0+3*c_6*y_0**2+y_0**3)+yx5*(2*c_0*c_6**2+4*c_0*c_6*y_0+2*c_0*y_0**2-2*c_1*c_6**2*y_0+c_1*c_6**2-4*c_1*c_6*y_0**2+2*c_1*c_6*y_0-2*c_1*y_0**3+c_1*y_0**2-2*c_2*c_6*y_0*y_2+c_2*c_6*y_2+2*c_2*c_6*yx5-2*c_2*y_0**2*y_2)/(c_6**2+2*c_6*y_0+y_0**2)-yx7*(2*c_2*c_6*y_2*yx5-c_4*c_6**3*y_1-3*c_4*c_6**2*y_0*y_1-3*c_4*c_6*y_0**2*y_1-c_4*y_0**3*y_1+c_5*c_6**3*y_2+3*c_5*c_6**2*y_0*y_2+3*c_5*c_6*y_0**2*y_2+c_5*y_0**3*y_2)/(c_6**3+3*c_6**2*y_0+3*c_6*y_0**2+y_0**3)+(-2*c_0*c_6*yx5-2*c_0*y_0*yx5+2*c_1*c_6*y_0*yx5+2*c_1*y_0**2*yx5+2*c_2*y_0*y_2*yx5-c_4*c_6*y_1*yx7-c_4*y_0*y_1*yx7+c_5*c_6*y_2*yx7+c_5*y_0*y_2*yx7)/(c_6+y_0)"],
                    ["-2*c_2*c_6*yx15*yx6/(c_6**3+3*c_6**2*y_0+3*c_6*y_0**2+y_0**3)+2*c_2*c_6*yx5*yx6/(c_6**2+2*c_6*y_0+y_0**2)+c_2*y_0*yx3/(c_6+y_0)-c_2*yx13*(2*c_6*y_0-c_6+2*y_0**2)/(c_6**2+2*c_6*y_0+y_0**2)-yx16*(2*c_2*c_6*y_0*y_2+2*c_2*y_0**2*y_2-c_2*y_0*y_2+2*c_2*y_2*(c_6+y_0)**2+(2*c_1+c_4)*(c_6+y_0)**3-(c_6+y_0)*(4*c_2*y_0*y_2-c_2*y_2))/(c_6+y_0)**3+yx17*(2*c_2*c_6*y_2*yx6+c_3*c_6**4+4*c_3*c_6**3*y_0+6*c_3*c_6**2*y_0**2+4*c_3*c_6*y_0**3+c_3*y_0**4)/(c_6**4+4*c_6**3*y_0+6*c_6**2*y_0**2+4*c_6*y_0**3+y_0**4)+yx6*(2*c_0-4*c_1*y_0+c_1+2*c_2*y_0**2*y_2/(c_6+y_0)**2-4*c_2*y_0*y_2/(c_6+y_0)-c_2*y_0*y_2/(c_6+y_0)**2+c_2*y_2/(c_6+y_0)-2*c_4*y_0+2*y_0*(c_1-c_2*y_0*y_2/(c_6+y_0)**2+c_2*y_2/(c_6+y_0)+c_4))-yx7*(2*c_2*c_6*y_2*yx6-c_3*c_6**3*y_0-3*c_3*c_6**2*y_0**2-3*c_3*c_6*y_0**3-c_3*y_0**4+c_4*c_6**3*y_1+3*c_4*c_6**2*y_0*y_1+3*c_4*c_6*y_0**2*y_1+c_4*y_0**3*y_1)/(c_6**3+3*c_6**2*y_0+3*c_6*y_0**2+y_0**3)+(-2*c_0*c_6*yx6-2*c_0*y_0*yx6+2*c_1*c_6*y_0*yx6+2*c_1*y_0**2*yx6+2*c_2*y_0*y_2*yx6-c_3*c_6*y_0*yx7-c_3*y_0**2*yx7+c_4*c_6*y_1*yx7+c_4*y_0*y_1*yx7)/(c_6+y_0)"],
                    ["-(-c_2*yx5*(c_6+y_0)*(c_6**3+3*c_6**2*y_0+3*c_6*y_0**2+y_0**3)*(3*c_6*y_0+3*c_6*yx7-c_6+3*y_0**2)*(c_6**4+4*c_6**3*y_0+6*c_6**2*y_0**2+4*c_6*y_0**3+y_0**4)+yx17*(c_6+y_0)*(c_6**2+2*c_6*y_0+y_0**2)*(c_6**3+3*c_6**2*y_0+3*c_6*y_0**2+y_0**3)*(3*c_1*c_6**4+12*c_1*c_6**3*y_0+18*c_1*c_6**2*y_0**2+12*c_1*c_6*y_0**3+3*c_1*y_0**4+3*c_2*c_6**3*y_2+6*c_2*c_6**2*y_0*y_2+3*c_2*c_6**2*y_2+3*c_2*c_6*y_0**2*y_2+3*c_2*c_6*y_0*y_2-3*c_2*c_6*y_2*yx7+c_2*c_6*y_2)-(c_6+y_0)*(-c_2*yx15*(3*c_6**2*y_0-3*c_6**2+6*c_6*y_0**2-3*c_6*y_0+3*c_6*yx7-c_6+3*y_0**3)+yx7*(3*c_0*c_6**3+9*c_0*c_6**2*y_0+9*c_0*c_6*y_0**2+3*c_0*y_0**3-3*c_1*c_6**3*y_0+3*c_1*c_6**3-9*c_1*c_6**2*y_0**2+9*c_1*c_6**2*y_0-9*c_1*c_6*y_0**3+9*c_1*c_6*y_0**2-3*c_1*y_0**4+3*c_1*y_0**3-3*c_2*c_6**2*y_0*y_2+3*c_2*c_6**2*y_2-6*c_2*c_6*y_0**2*y_2+3*c_2*c_6*y_0*y_2-3*c_2*c_6*y_2*yx7+c_2*c_6*y_2-3*c_2*y_0**3*y_2))*(c_6**2+2*c_6*y_0+y_0**2)*(c_6**4+4*c_6**3*y_0+6*c_6**2*y_0**2+4*c_6*y_0**3+y_0**4)-(c_6**2+2*c_6*y_0+y_0**2)*(c_6**3+3*c_6**2*y_0+3*c_6*y_0**2+y_0**3)*(c_6**4+4*c_6**3*y_0+6*c_6**2*y_0**2+4*c_6*y_0**3+y_0**4)*(-3*c_0*c_6*yx7+c_0*c_6-3*c_0*y_0*yx7+c_0*y_0+3*c_1*c_6*y_0*yx7-c_1*c_6*y_0+3*c_1*y_0**2*yx7-c_1*y_0**2+3*c_2*y_0*y_2*yx7-c_2*y_0*y_2))/((c_6+y_0)*(c_6**2+2*c_6*y_0+y_0**2)*(c_6**3+3*c_6**2*y_0+3*c_6*y_0**2+y_0**3)*(c_6**4+4*c_6**3*y_0+6*c_6**2*y_0**2+4*c_6*y_0**3+y_0**4))"]
            ])
        central_from_raw_exprs = to_sympy_matrix(
                    [["x_0_0_2-y_2**2"],
                    ["x_0_1_1-y_1*y_2"],
                    ["x_0_2_0-y_1**2"],
                    ["x_1_0_1-y_0*y_2"],
                    ["x_1_1_0-y_0*y_1"],
                    ["x_2_0_0-y_0**2"],
                    ["-3*x_0_0_2*y_2+x_0_0_3+2*y_2**3"],
                    ["-x_0_0_2*y_1-2*x_0_1_1*y_2+x_0_1_2+2*y_1*y_2**2"],
                    ["-2*x_0_1_1*y_1-x_0_2_0*y_2+x_0_2_1+2*y_1**2*y_2"],
                    ["-3*x_0_2_0*y_1+x_0_3_0+2*y_1**3"],
                    ["-x_0_0_2*y_0-2*x_1_0_1*y_2+x_1_0_2+2*y_0*y_2**2"],
                    ["-x_0_1_1*y_0-x_1_0_1*y_1-x_1_1_0*y_2+x_1_1_1+2*y_0*y_1*y_2"],
                    ["-x_0_2_0*y_0-2*x_1_1_0*y_1+x_1_2_0+2*y_0*y_1**2"],
                    ["-2*x_1_0_1*y_0-x_2_0_0*y_2+x_2_0_1+2*y_0**2*y_2"],
                    ["-2*x_1_1_0*y_0-x_2_0_0*y_1+x_2_1_0+2*y_0**2*y_1"],
                    ["-3*x_2_0_0*y_0+x_3_0_0+2*y_0**3"]
         ])


        k_counter = [
                    Moment([0, 0, 0], symbol=sympy.Integer(1)),
                    Moment([1, 0, 0], symbol=sympy.Symbol("y_0")),
                    Moment([0, 1, 0], symbol=sympy.Symbol("y_1")),
                    Moment([0, 0, 1], symbol=sympy.Symbol("y_2")),
                    Moment([0, 0, 2], symbol=sympy.Symbol("x_0_0_2")),
                    Moment([0, 1, 1], symbol=sympy.Symbol("x_0_1_1")),
                    Moment([0, 2, 0], symbol=sympy.Symbol("x_0_2_0")),
                    Moment([1, 0, 1], symbol=sympy.Symbol("x_1_0_1")),
                    Moment([1, 1, 0], symbol=sympy.Symbol("x_1_1_0")),
                    Moment([2, 0, 0], symbol=sympy.Symbol("x_2_0_0")),
                    Moment([0, 0, 3], symbol=sympy.Symbol("x_0_0_3")),
                    Moment([0, 1, 2], symbol=sympy.Symbol("x_0_1_2")),
                    Moment([0, 2, 1], symbol=sympy.Symbol("x_0_2_1")),
                    Moment([0, 3, 0], symbol=sympy.Symbol("x_0_3_0")),
                    Moment([1, 0, 2], symbol=sympy.Symbol("x_1_0_2")),
                    Moment([1, 1, 1], symbol=sympy.Symbol("x_1_1_1")),
                    Moment([1, 2, 0], symbol=sympy.Symbol("x_1_2_0")),
                    Moment([2, 0, 1], symbol=sympy.Symbol("x_2_0_1")),
                    Moment([2, 1, 0], symbol=sympy.Symbol("x_2_1_0")),
                    Moment([3, 0, 0], symbol=sympy.Symbol("x_3_0_0"))
                ]

        n_moments = 3
        species = to_sympy_matrix([["y_0"],["y_1"],["y_2"]])
        prob_moments = self.__problem_moments
        expected = to_sympy_matrix([
                    ["c_0-c_1*y_0-(c_2*c_6*yx5)/(c_6+y_0) ** 2-(c_2*y_0*y_2)/(c_6+y_0)+(c_2*c_6*y_2*yx7)/(c_6+y_0) ** 3+(c_2*c_6*yx5*(yx5*y_0 ** 2+2*y_2*yx7*y_0+yx5*yx7))/(y_0 ** 2*y_2*(c_6+y_0) ** 3)-(c_2*c_6*y_2*yx7 ** 2*(3*y_0 ** 2+yx7))/(y_0 ** 3*(c_6+y_0) ** 4)"],
                    ["c_3*y_0-c_4*y_1"],
                    ["c_4*y_1-c_5*y_2"],
                    ["c_4*y_1+c_5*y_2+2*c_4*yx3-2*c_5*yx2"],
                    ["c_3*yx5-c_4*yx3-c_4*y_1+c_4*yx4-c_5*yx3"],
                    ["c_3*y_0+c_4*y_1-2*c_4*yx4+2*c_3*yx6"],
                    ["-(c_2*y_0 ** 5*y_2 ** 2*yx2+c_1*y_0 ** 5*y_2 ** 2*yx5-c_4*y_0 ** 5*y_2 ** 2*yx6+c_5*y_0 ** 5*y_2 ** 2*yx5+2*c_2*c_6*y_0 ** 4*y_2 ** 2*yx2+3*c_1*c_6*y_0 ** 4*y_2 ** 2*yx5+c_2*c_6*y_0 ** 3*y_2 ** 3*yx5-3*c_4*c_6*y_0 ** 4*y_2 ** 2*yx6+3*c_5*c_6*y_0 ** 4*y_2 ** 2*yx5+c_2*c_6*y_0 ** 2*yx2*yx5 ** 2+c_2*c_6 ** 2*y_0*yx2*yx5 ** 2-c_2*c_6*y_2 ** 2*yx5 ** 2*yx7+c_2*c_6 ** 2*y_0 ** 3*y_2 ** 2*yx2+3*c_1*c_6 ** 2*y_0 ** 3*y_2 ** 2*yx5+c_1*c_6 ** 3*y_0 ** 2*y_2 ** 2*yx5+c_2*c_6 ** 2*y_0*y_2 ** 2*yx5 ** 2+c_2*c_6 ** 2*y_0 ** 2*y_2 ** 3*yx5-3*c_4*c_6 ** 2*y_0 ** 3*y_2 ** 2*yx6-c_4*c_6 ** 3*y_0 ** 2*y_2 ** 2*yx6+3*c_5*c_6 ** 2*y_0 ** 3*y_2 ** 2*yx5+c_5*c_6 ** 3*y_0 ** 2*y_2 ** 2*yx5+2*c_2*c_6*y_0 ** 3*y_2*yx2*yx5-2*c_2*c_6*y_0*y_2 ** 3*yx5*yx7+2*c_2*c_6 ** 2*y_0 ** 2*y_2*yx2*yx5)/(y_0 ** 2*y_2 ** 2*(c_6+y_0) ** 3)"],
                    ["-(c_2*y_0 ** 5*y_1*y_2*yx3+c_1*y_0 ** 5*y_1*y_2*yx6-c_3*y_0 ** 5*y_1*y_2*yx7+c_4*y_0 ** 5*y_1*y_2*yx6-c_2*c_6*y_2 ** 2*yx6 ** 2*yx7-c_2*c_6*y_0 ** 2*y_2 ** 2*yx6 ** 2+c_2*c_6 ** 2*y_0 ** 2*y_1*y_2 ** 2*yx6+2*c_2*c_6*y_0 ** 4*y_1*y_2*yx3+3*c_1*c_6*y_0 ** 4*y_1*y_2*yx6-3*c_3*c_6*y_0 ** 4*y_1*y_2*yx7+3*c_4*c_6*y_0 ** 4*y_1*y_2*yx6+c_2*c_6*y_0 ** 3*y_1*yx3*yx5+c_2*c_6*y_0 ** 3*y_2*yx3*yx6+c_2*c_6*y_0 ** 2*yx3*yx5*yx6+c_2*c_6 ** 2*y_0*yx3*yx5*yx6+c_2*c_6 ** 2*y_0 ** 3*y_1*y_2*yx3+3*c_1*c_6 ** 2*y_0 ** 3*y_1*y_2*yx6+c_1*c_6 ** 3*y_0 ** 2*y_1*y_2*yx6+c_2*c_6*y_0 ** 3*y_1*y_2 ** 2*yx6-3*c_3*c_6 ** 2*y_0 ** 3*y_1*y_2*yx7-c_3*c_6 ** 3*y_0 ** 2*y_1*y_2*yx7+3*c_4*c_6 ** 2*y_0 ** 3*y_1*y_2*yx6+c_4*c_6 ** 3*y_0 ** 2*y_1*y_2*yx6+c_2*c_6 ** 2*y_0 ** 2*y_1*yx3*yx5+c_2*c_6 ** 2*y_0 ** 2*y_2*yx3*yx6+c_2*c_6*y_0 ** 2*y_1*y_2*yx5*yx6+c_2*c_6 ** 2*y_0*y_1*y_2*yx5*yx6-2*c_2*c_6*y_0*y_1*y_2 ** 2*yx6*yx7)/(y_0 ** 2*y_1*y_2*(c_6+y_0) ** 3)"],
                    ["-(-c_1*c_6 ** 4*y_0 ** 4*y_2+2*c_1*c_6 ** 4*y_0 ** 3*y_2*yx7-c_0*c_6 ** 4*y_0 ** 3*y_2-4*c_1*c_6 ** 3*y_0 ** 5*y_2-c_2*c_6 ** 3*y_0 ** 4*y_2 ** 2+2*c_2*c_6 ** 3*y_0 ** 4*y_2*yx5+8*c_1*c_6 ** 3*y_0 ** 4*y_2*yx7-4*c_0*c_6 ** 3*y_0 ** 4*y_2+2*c_2*c_6 ** 3*y_0 ** 3*y_2 ** 2*yx7-c_2*c_6 ** 3*y_0 ** 3*y_2*yx5+2*c_2*c_6 ** 3*y_0 ** 3*yx5 ** 2+4*c_2*c_6 ** 3*y_0 ** 2*y_2*yx5*yx7+2*c_2*c_6 ** 3*y_0*yx5 ** 2*yx7-6*c_1*c_6 ** 2*y_0 ** 6*y_2-3*c_2*c_6 ** 2*y_0 ** 5*y_2 ** 2+6*c_2*c_6 ** 2*y_0 ** 5*y_2*yx5+12*c_1*c_6 ** 2*y_0 ** 5*y_2*yx7-6*c_0*c_6 ** 2*y_0 ** 5*y_2+4*c_2*c_6 ** 2*y_0 ** 4*y_2 ** 2*yx7-2*c_2*c_6 ** 2*y_0 ** 4*y_2*yx5+4*c_2*c_6 ** 2*y_0 ** 4*yx5 ** 2+c_2*c_6 ** 2*y_0 ** 3*y_2 ** 2*yx7+8*c_2*c_6 ** 2*y_0 ** 3*y_2*yx5*yx7+c_2*c_6 ** 2*y_0 ** 3*yx5 ** 2-6*c_2*c_6 ** 2*y_0 ** 2*y_2 ** 2*yx7 ** 2+2*c_2*c_6 ** 2*y_0 ** 2*y_2*yx5*yx7+4*c_2*c_6 ** 2*y_0 ** 2*yx5 ** 2*yx7+c_2*c_6 ** 2*y_0*yx5 ** 2*yx7-2*c_2*c_6 ** 2*y_2 ** 2*yx7 ** 3-4*c_1*c_6*y_0 ** 7*y_2-3*c_2*c_6*y_0 ** 6*y_2 ** 2+6*c_2*c_6*y_0 ** 6*y_2*yx5+8*c_1*c_6*y_0 ** 6*y_2*yx7-4*c_0*c_6*y_0 ** 6*y_2+2*c_2*c_6*y_0 ** 5*y_2 ** 2*yx7-c_2*c_6*y_0 ** 5*y_2*yx5+2*c_2*c_6*y_0 ** 5*yx5 ** 2+c_2*c_6*y_0 ** 4*y_2 ** 2*yx7+4*c_2*c_6*y_0 ** 4*y_2*yx5*yx7+c_2*c_6*y_0 ** 4*yx5 ** 2-6*c_2*c_6*y_0 ** 3*y_2 ** 2*yx7 ** 2+2*c_2*c_6*y_0 ** 3*y_2*yx5*yx7+2*c_2*c_6*y_0 ** 3*yx5 ** 2*yx7-3*c_2*c_6*y_0 ** 2*y_2 ** 2*yx7 ** 2+c_2*c_6*y_0 ** 2*yx5 ** 2*yx7-2*c_2*c_6*y_0*y_2 ** 2*yx7 ** 3-c_2*c_6*y_2 ** 2*yx7 ** 3-c_1*y_0 ** 8*y_2-c_2*y_0 ** 7*y_2 ** 2+2*c_2*y_0 ** 7*y_2*yx5+2*c_1*y_0 ** 7*y_2*yx7-c_0*y_0 ** 7*y_2)/(y_0 ** 3*y_2*(c_6+y_0) ** 4)"]
                ])
        closer = LogNormalCloser(3,multivariate=True)
        answer, lhs_answer = closer.parametric_closer_wrapper(mfk, central_from_raw_exprs, species, k_counter, prob_moments)

        self.assertTrue(sympy_expressions_equal(answer, expected))