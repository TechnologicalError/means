import unittest
import means
from means.util.sympyhelpers import to_sympy_matrix
from means.core import ODEProblem, ODETermBase, Moment, VarianceTerm
from means.simulation import Simulation
from numpy.testing import assert_array_almost_equal
import numpy as np
import random
from sympy import Symbol, MutableDenseMatrix, symbols, Float


class ConstantDerivativesProblem(ODEProblem):
    def __init__(self):
        super(ConstantDerivativesProblem, self).__init__(method=None,
                                                         left_hand_side_descriptors=[ODETermBase('y_1'), ODETermBase('y_2')],
                                                         right_hand_side=['c_1', 'c_2'],
                                                         parameters=['c_1', 'c_2'])

class TestSimulate(unittest.TestCase):

    def test_simulation_of_simple_model(self):
        """
        Given the simplest possible problem, the one with constant derivatives,
        results produced by the simulation should be easily predictable.
        """
        s = Simulation(ConstantDerivativesProblem())

        trajectories = s.simulate_system(parameters=[0, 1],
                                         initial_conditions=[3, 2],
                                         timepoints=[0, 1, 2, 3])
        trajectories_dict = {trajectory.description.symbol: trajectory for trajectory in trajectories}
        y_1_trajectory = trajectories_dict[Symbol('y_1')]
        y_2_trajectory = trajectories_dict[Symbol('y_2')]

        assert_array_almost_equal(y_1_trajectory.values, [3, 3, 3, 3])
        assert_array_almost_equal(y_2_trajectory.values, [2, 3, 4, 5])


class TestSimulateWithSensitivities(unittest.TestCase):


    def test_model_in_paper(self):
        """
        Given the model in the Ale et. al Paper, and the initial parameters,
        the simulation with sensitivities result should be similar to the one described in paper, within minimal margin
        of error.
        """
        parameters = [1.66e-3, 0.2]
        initial_conditions = [301, 0]
        timepoints = np.arange(0, 20, 0.1)

        problem = ODEProblem('MNA',
                             [Moment([1, 0], 'x_1'),
                              Moment([0, 1], 'x_2'),
                              Moment([0, 2], 'yx1'),
                              Moment([1, 1], 'yx2'),
                              Moment([2, 0], 'yx3')],
                             to_sympy_matrix(['-2*k_1*x_1*(x_1 - 1) - 2*k_1*yx3 + 2*k_2*x_2',
                                              'k_1*x_1*(x_1 - 1) + k_1*yx3 - k_2*x_2',

                                              'k_1*x_1**2 - k_1*x_1 + 2*k_1*yx2*(2*x_1 - 1) '
                                              '+ k_1*yx3 + k_2*x_2 - 2*k_2*yx1',

                                              '-2*k_1*x_1**2 + 2*k_1*x_1 + k_1*yx3*(2*x_1 - 3) '
                                              '- 2*k_2*x_2 + 2*k_2*yx1 - yx2*(4*k_1*x_1 '
                                              '- 2*k_1 + k_2)',

                                              '4*k_1*x_1**2 - 4*k_1*x_1 - 8*k_1*yx3*(x_1 - 1)'
                                              ' + 4*k_2*x_2 + 4*k_2*yx2'
                             ]),
                             ['k_1', 'k_2']
                             )

        simulation = means.simulation.SimulationWithSensitivities(problem)
        trajectories = simulation.simulate_system(parameters, initial_conditions, timepoints)

        answers = {}

        # Trajectory value, sensitivity wrt k_1, sensitivity wrt k_2
        answers[Moment([1, 0], 'x_1')] = (107.94814091151031, -25415.418060971126, 210.94691048709868)
        answers[Moment([0, 1], 'x_2')] = (96.525929544244818, 12707.709030485566, -105.47345524354937)

        seen_answers = set()
        for trajectory in trajectories:
            # There should be one sensitivity trajectory for each parameter
            self.assertEqual(len(trajectory.sensitivity_data), len(parameters))

            # Check the ones we have answers for
            answer = None
            try:
                answer = answers[trajectory.description]
            except KeyError:
                continue

            seen_answers.add(trajectory.description)

            self.assertAlmostEqual(answer[0], trajectory.values[-1], places=6)
            self.assertAlmostEqual(answer[1], trajectory.sensitivity_data[0].values[-1], places=6)
            self.assertAlmostEqual(answer[2], trajectory.sensitivity_data[1].values[-1], places=6)

        self.assertEqual(len(seen_answers), len(answers), msg='Some of the trajectories for moments were not returned')


class TestSimulateRegressionForPopularModels(unittest.TestCase):

    def setUp(self):
        np.random.seed(42)
        random.seed(42)

    def test_p53_3_moments(self):

        # This is just a hardcoded result of MomentExpansionApproximation(MODEL_P53,3).run()
        y_0, y_1, y_2 = symbols(['y_0', 'y_1', 'y_2'])

        yx1, yx2, yx3, yx4, yx5, yx6 = symbols(['yx1', 'yx2', 'yx3', 'yx4', 'yx5', 'yx6'])
        yx7, yx8, yx9, yx10, yx11, yx12 = symbols(['yx7', 'yx8', 'yx9', 'yx10', 'yx11', 'yx12'])
        yx13, yx14, yx15, yx16 = symbols(['yx13', 'yx14', 'yx15', 'yx16'])

        c_0, c_1, c_2, c_3, c_4, c_5, c_6 = symbols(['c_0', 'c_1', 'c_2', 'c_3', 'c_4', 'c_5', 'c_6'])

        left_hand_side_descriptors = [Moment(np.array([1, 0, 0]), symbol=y_0),
                         Moment(np.array([0, 1, 0]), symbol=y_1),
                         Moment(np.array([0, 0, 1]), symbol=y_2),
                         Moment(np.array([0, 0, 2]), symbol=yx1),
                         Moment(np.array([0, 0, 3]), symbol=yx2),
                         Moment(np.array([0, 1, 1]), symbol=yx3),
                         Moment(np.array([0, 1, 2]), symbol=yx4),
                         Moment(np.array([0, 2, 0]), symbol=yx5),
                         Moment(np.array([0, 2, 1]), symbol=yx6),
                         Moment(np.array([0, 3, 0]), symbol=yx7),
                         Moment(np.array([1, 0, 1]), symbol=yx8),
                         Moment(np.array([1, 0, 2]), symbol=yx9),
                         Moment(np.array([1, 1, 0]), symbol=yx10),
                         Moment(np.array([1, 1, 1]), symbol=yx11),
                         Moment(np.array([1, 2, 0]), symbol=yx12),
                         Moment(np.array([2, 0, 0]), symbol=yx13),
                         Moment(np.array([2, 0, 1]), symbol=yx14),
                         Moment(np.array([2, 1, 0]), symbol=yx15),
                         Moment(np.array([3, 0, 0]), symbol=yx16)]

        constants = [c_0, c_1, c_2, c_3, c_4, c_5, c_6]

        right_hand_side = MutableDenseMatrix([[(-c_2*c_6*y_2*yx16 - c_2*c_6*yx8*(c_6 + y_0)**2 + c_2*c_6*(c_6 + y_0)*(y_2*yx13 + yx14) - c_2*y_0*y_2*(c_6 + y_0)**3 + (c_0 - c_1*y_0)*(c_6 + y_0)**4)/(c_6 + y_0)**4], [c_3*y_0 - c_4*y_1], [c_4*y_1 - c_5*y_2], [c_4*y_1 + 2*c_4*yx3 + c_5*y_2 - 2*c_5*yx1], [c_4*y_1 + 3*c_4*yx3 + 3*c_4*yx4 - c_5*y_2 + 3*c_5*yx1 - 3*c_5*yx2], [c_3*yx8 - c_4*y_1 + c_4*yx5 - yx3*(c_4 + c_5)], [c_3*yx9 - c_4*y_1 - 2*c_4*yx3 - c_4*yx4 + c_4*yx5 + 2*c_4*yx6 + c_5*yx3 - 2*c_5*yx4], [c_3*y_0 + 2*c_3*yx10 + c_4*y_1 - 2*c_4*yx5], [2*c_3*yx11 + c_3*yx8 + c_4*y_1 + c_4*yx3 - 2*c_4*yx5 - 2*c_4*yx6 + c_4*yx7 - c_5*yx6], [c_3*y_0 + 3*c_3*yx10 + 3*c_3*yx12 - c_4*y_1 + 3*c_4*yx5 - 3*c_4*yx7], [(c_2*c_6*y_2*yx14 - c_2*y_0*yx1*(c_6 + y_0)**2 + c_4*yx10*(c_6 + y_0)**3 - (c_6 + y_0)*(c_2*c_6*yx9 + yx8*(c_2*c_6*y_2 + (c_1 + c_5)*(c_6 + y_0)**2)))/(c_6 + y_0)**3], [(c_2*c_6*y_2*yx1*yx16 - c_2*c_6*yx1*(c_6 + y_0)*(y_2*yx13 + yx14) + c_4*(c_6 + y_0)**4*(yx10 + 2*yx11) + (c_6 + y_0)**3*(-c_0*c_6*yx1 - c_0*y_0*yx1 + c_1*c_6*y_0*yx1 + c_1*y_0**2*yx1 + c_2*y_0*y_2*yx1 - c_2*y_0*yx2 - 2*c_4*c_6*y_1*yx8 - 2*c_4*y_0*y_1*yx8 + 2*c_5*c_6*y_2*yx8 + 2*c_5*y_0*y_2*yx8 - yx1*(c_2*y_0*y_2 - (c_0 - c_1*y_0)*(c_6 + y_0))) + (c_6 + y_0)**2*(yx8*(c_2*c_6*yx1 + (c_6 + y_0)**2*(2*c_4*y_1 - 2*c_5*y_2 + c_5)) - yx9*(c_2*c_6*y_2 + (c_1 + 2*c_5)*(c_6 + y_0)**2)))/(c_6 + y_0)**4], [(c_2*c_6*y_2*yx15 - c_2*y_0*yx3*(c_6 + y_0)**2 + c_3*yx13*(c_6 + y_0)**3 - (c_6 + y_0)*(c_2*c_6*yx11 + yx10*(c_2*c_6*y_2 + (c_1 + c_4)*(c_6 + y_0)**2)))/(c_6 + y_0)**3], [(c_2*c_6*y_2*yx16*yx3 + (c_6 + y_0)**4*(c_4*yx12 - yx10*(-c_4*y_1 + c_4 + c_5*y_2)) + (c_6 + y_0)**3*(-c_0*c_6*yx3 - c_0*y_0*yx3 + c_1*c_6*y_0*yx3 + c_1*y_0**2*yx3 + c_2*y_0*y_2*yx3 - c_2*y_0*yx4 - c_3*c_6*y_0*yx8 - c_3*y_0**2*yx8 - c_4*c_6*y_1*yx10 + c_4*c_6*y_1*yx8 - c_4*y_0*y_1*yx10 + c_4*y_0*y_1*yx8 + c_5*c_6*y_2*yx10 + c_5*y_0*y_2*yx10 - yx3*(-c_0*c_6 - c_0*y_0 + c_1*c_6*y_0 + c_1*y_0**2 + c_2*y_0*y_2)) + (c_6 + y_0)**2*(-yx11*(c_2*c_6*y_2 + (c_6 + y_0)**2*(c_1 + c_4 + c_5)) + yx8*(c_2*c_6*yx3 + (c_6 + y_0)**2*(c_3*y_0 - c_4*y_1))) - (c_6 + y_0)*(c_2*c_6*y_2*yx13*yx3 + yx14*(c_2*c_6*yx3 - c_3*(c_6 + y_0)**3)))/(c_6 + y_0)**4], [(c_2*c_6*y_2*yx16*yx5 + (c_6 + y_0)**4*(2*c_3*yx15 + yx10*(2*c_3*y_0 - 2*c_4*y_1 + c_4)) + (c_6 + y_0)**3*(-c_0*c_6*yx5 - c_0*y_0*yx5 + c_1*c_6*y_0*yx5 + c_1*y_0**2*yx5 + c_2*y_0*y_2*yx5 - c_2*y_0*yx6 - 2*c_3*c_6*y_0*yx10 - 2*c_3*y_0**2*yx10 + 2*c_4*c_6*y_1*yx10 + 2*c_4*y_0*y_1*yx10 - yx5*(c_2*y_0*y_2 - (c_0 - c_1*y_0)*(c_6 + y_0))) + (c_6 + y_0)**2*(c_2*c_6*yx5*yx8 - yx12*(c_2*c_6*y_2 + (c_1 + 2*c_4)*(c_6 + y_0)**2)) - (c_6 + y_0)*(c_2*c_6*yx14*yx5 + yx13*(c_2*c_6*y_2*yx5 - c_3*(c_6 + y_0)**3)))/(c_6 + y_0)**4], [(c_2*y_2*yx16*(c_6*(2*y_0 + 1) + 2*y_0**2 - 4*y_0*(c_6 + y_0) + 2*(c_6 + y_0)**2) + c_2*yx8*(c_6 + y_0)**2*(2*c_6*y_0 + c_6 - 2*y_0*(2*c_6 + y_0)) + (c_6 + y_0)**3*(c_0*c_6 + c_0*y_0 + c_1*c_6*y_0 + c_1*y_0**2 + c_2*y_0*y_2) - (c_6 + y_0)*(c_2*yx14*(c_6*(2*y_0 + 1) + 2*y_0**2 - 4*y_0*(c_6 + y_0) + 2*(c_6 + y_0)**2) + yx13*(2*c_1*(c_6 + y_0)**3 + c_2*c_6*y_2*(2*y_0 + 1) + 2*c_2*y_2*(y_0**2 - 2*y_0*(c_6 + y_0) + (c_6 + y_0)**2))))/(c_6 + y_0)**4], [(2*c_2*c_6*y_2*yx16*yx8*(c_6 + y_0)**3 + c_4*yx15*(c_6 + y_0)**3*(c_6**4 + 4*c_6**3*y_0 + 6*c_6**2*y_0**2 + 4*c_6*y_0**3 + y_0**4) - yx13*(2*c_2*c_6*y_2*yx8 + (c_6 + y_0)**3*(-c_4*y_1 + c_5*y_2))*(c_6**4 + 4*c_6**3*y_0 + 6*c_6**2*y_0**2 + 4*c_6*y_0**3 + y_0**4) - yx14*(2*c_2*y_2*(c_6 + y_0)**2 + c_2*(-2*c_6*y_0*y_2 + c_6*y_2 + 2*c_6*yx8 - 2*y_0**2*y_2) + (2*c_1 + c_5)*(c_6 + y_0)**3)*(c_6**4 + 4*c_6**3*y_0 + 6*c_6**2*y_0**2 + 4*c_6*y_0**3 + y_0**4) + (c_6 + y_0)**2*(c_6**4 + 4*c_6**3*y_0 + 6*c_6**2*y_0**2 + 4*c_6*y_0**3 + y_0**4)*(-2*c_0*c_6*yx8 - 2*c_0*y_0*yx8 + 2*c_1*c_6*y_0*yx8 + 2*c_1*y_0**2*yx8 + 2*c_2*y_0*y_2*yx8 + c_2*y_0*yx1 - c_4*c_6*y_1*yx13 - c_4*y_0*y_1*yx13 + c_5*c_6*y_2*yx13 + c_5*y_0*y_2*yx13) + (c_6 + y_0)*(c_2*yx9*(2*c_6*y_0 + c_6 - 2*y_0*(2*c_6 + y_0)) + yx8*(-2*c_2*c_6*y_0*y_2 + c_2*c_6*y_2 + 2*c_2*c_6*yx8 - 2*c_2*y_0**2*y_2 + (c_6 + y_0)**2*(2*c_0 - 2*c_1*y_0 + c_1)))*(c_6**4 + 4*c_6**3*y_0 + 6*c_6**2*y_0**2 + 4*c_6*y_0**3 + y_0**4))/((c_6 + y_0)**3*(c_6**4 + 4*c_6**3*y_0 + 6*c_6**2*y_0**2 + 4*c_6*y_0**3 + y_0**4))], [(c_1*c_6**4*yx10 - 2*c_1*c_6**4*yx15 + 4*c_1*c_6**3*y_0*yx10 - 8*c_1*c_6**3*y_0*yx15 + 6*c_1*c_6**2*y_0**2*yx10 - 12*c_1*c_6**2*y_0**2*yx15 + 4*c_1*c_6*y_0**3*yx10 - 8*c_1*c_6*y_0**3*yx15 + c_1*y_0**4*yx10 - 2*c_1*y_0**4*yx15 - 2*c_2*c_6**3*y_0*yx11 + c_2*c_6**3*y_0*yx3 + c_2*c_6**3*y_2*yx10 - 2*c_2*c_6**3*y_2*yx15 + 2*c_2*c_6**3*yx10*yx8 + c_2*c_6**3*yx11 - 6*c_2*c_6**2*y_0**2*yx11 + 3*c_2*c_6**2*y_0**2*yx3 + 2*c_2*c_6**2*y_0*y_2*yx10 - 4*c_2*c_6**2*y_0*y_2*yx15 + 4*c_2*c_6**2*y_0*yx10*yx8 + 2*c_2*c_6**2*y_0*yx11 - 2*c_2*c_6**2*y_2*yx10*yx13 - c_2*c_6**2*y_2*yx15 - 2*c_2*c_6**2*yx10*yx14 - 6*c_2*c_6*y_0**3*yx11 + 3*c_2*c_6*y_0**3*yx3 + c_2*c_6*y_0**2*y_2*yx10 - 2*c_2*c_6*y_0**2*y_2*yx15 + 2*c_2*c_6*y_0**2*yx10*yx8 + c_2*c_6*y_0**2*yx11 - 2*c_2*c_6*y_0*y_2*yx10*yx13 - c_2*c_6*y_0*y_2*yx15 - 2*c_2*c_6*y_0*yx10*yx14 + 2*c_2*c_6*y_2*yx10*yx16 - 2*c_2*y_0**4*yx11 + c_2*y_0**4*yx3 + c_3*c_6**4*yx16 + 4*c_3*c_6**3*y_0*yx16 + 6*c_3*c_6**2*y_0**2*yx16 + 4*c_3*c_6*y_0**3*yx16 + c_3*y_0**4*yx16 - c_4*c_6**4*yx15 - 4*c_4*c_6**3*y_0*yx15 - 6*c_4*c_6**2*y_0**2*yx15 - 4*c_4*c_6*y_0**3*yx15 - c_4*y_0**4*yx15)/(c_6**4 + 4*c_6**3*y_0 + 6*c_6**2*y_0**2 + 4*c_6*y_0**3 + y_0**4)], [(-c_2*yx14*(c_6 + y_0)**4*(c_6**2 + 2*c_6*y_0 + y_0**2)*(3*c_6**2*y_0 - 3*c_6**2 + 6*c_6*y_0**2 - 3*c_6*y_0 + 3*c_6*yx13 - c_6 + 3*y_0**3) + c_2*yx8*(c_6 + y_0)**4*(c_6**3 + 3*c_6**2*y_0 + 3*c_6*y_0**2 + y_0**3)*(3*c_6*y_0 + 3*c_6*yx13 - c_6 + 3*y_0**2) - yx13*(c_6 + y_0)*(c_6**2 + 2*c_6*y_0 + y_0**2)*(3*c_2*y_2*(c_6 + y_0)**2*(y_0 - 1) + c_2*y_2*(3*c_6*y_0 + 3*c_6*yx13 - c_6 + 3*y_0**2) + 3*(c_6 + y_0)**3*(-c_0 + c_1*y_0 - c_1))*(c_6**3 + 3*c_6**2*y_0 + 3*c_6*y_0**2 + y_0**3) - yx16*(c_6**2 + 2*c_6*y_0 + y_0**2)*(c_6**3 + 3*c_6**2*y_0 + 3*c_6*y_0**2 + y_0**3)*(3*c_1*(c_6 + y_0)**4 + 3*c_2*y_2*(c_6 + y_0)**3 + 3*c_2*y_2*(c_6 + y_0)**2*(-y_0 + 1) + c_2*y_2*(-3*c_6*y_0 - 3*c_6*yx13 + c_6 - 3*y_0**2)) + (c_6 + y_0)**3*(c_6**2 + 2*c_6*y_0 + y_0**2)*(c_6**3 + 3*c_6**2*y_0 + 3*c_6*y_0**2 + y_0**3)*(-3*c_0*c_6*yx13 + c_0*c_6 - 3*c_0*y_0*yx13 + c_0*y_0 + 3*c_1*c_6*y_0*yx13 - c_1*c_6*y_0 + 3*c_1*y_0**2*yx13 - c_1*y_0**2 + 3*c_2*y_0*y_2*yx13 - c_2*y_0*y_2))/((c_6 + y_0)**4*(c_6**2 + 2*c_6*y_0 + y_0**2)*(c_6**3 + 3*c_6**2*y_0 + 3*c_6*y_0**2 + y_0**3))]])

        problem = ODEProblem('MEA', left_hand_side_descriptors, right_hand_side, constants)

        simulation = Simulation(problem, rtol=1e-4, atol=1e-4)
        timepoints = np.arange(0, 20.5, 0.5)

        parameters = [90, 0.002, 1.2, 1.1, 0.8, 0.96, 0.01]
        initial_conditions = [80, 40, 60]

        simulated_trajectories = simulation.simulate_system(parameters, initial_conditions, timepoints)
        answer_lookup = {trajectory.description: trajectory.values for trajectory in simulated_trajectories}

        answers = np.array([
            [80.0, 91.2610807076, 102.686308277, 109.933251768, 110.948696417, 105.350207732, 94.0538241118, 78.9247702823, 62.3869295343, 47.0019597953, 35.0615887795, 28.2435001275, 27.3706668841, 32.3183272998, 42.0889917996, 54.9985562653, 68.9536965049, 81.7868285817, 91.590181638, 96.9959626072, 97.3626161669, 92.8421227407, 84.3245022471, 73.2733227635, 61.4768081305, 50.7635432029, 42.7220336223, 38.4670712045, 38.4878572162, 42.6007305815, 50.0088503072, 59.4486640666, 69.3994972516, 78.325357481, 84.9095443302, 88.2462118471, 87.9614728036, 84.2484274164, 77.8144016961, 69.7520532558, 61.3570863088],
            [40.0, 65.67706231, 88.2517032438, 107.667075516, 122.502876904, 131.296472003, 133.22065582, 128.379472101, 117.838728402, 103.460947373, 87.6050573058, 72.7539287431, 61.1324229109, 54.3761261219, 53.3084501104, 57.8539321419, 67.0883335638, 79.4118879044, 92.820728146, 105.228336185, 114.786820513, 120.158106519, 120.69673887, 116.521202512, 108.462448437, 97.908878415, 86.5720807933, 76.212259156, 68.3672951211, 64.1267747022, 63.985477403, 67.7941572281, 74.8090753242, 83.8294015754, 93.398727104, 102.037235706, 108.467982327, 111.802993296, 111.662455863, 108.211625489, 102.113232822],
            [60.0, 54.3421911673, 58.433352737, 67.62295537, 78.7343069524, 89.3188813344, 97.4939357646, 101.98752539, 102.212678492, 98.2878896186, 90.9725166746, 81.5172966828, 71.4503704562, 62.33062923, 55.5071089948, 51.9222110377, 51.9866764605, 55.539017734, 61.8937342304, 69.9671824676, 78.4588728181, 86.0583613265, 91.6449919912, 94.4512916827, 94.164947896, 90.9575846067, 85.4388622208, 78.5454737846, 71.3848016628, 65.0587634991, 60.4959119013, 58.3174748724, 58.7559208163, 61.6358077019, 66.4173656406, 72.2937019644, 78.3246420494, 83.5853720438, 87.3066233819, 88.9853994161, 88.4506279276],
            [0.0, 28.5993789021, 45.7748080397, 66.836496808, 97.0947504774, 135.324576427, 175.918469516, 212.310008129, 240.37572115, 260.107256632, 274.853956826, 288.844496157, 304.597909883, 321.741857629, 337.782448469, 350.164949487, 358.251540145, 363.97467871, 370.904011301, 382.309921105, 399.395865304, 420.697371604, 442.899622744, 462.537014302, 477.635100049, 488.327249145, 496.300255401, 503.514746932, 511.012713546, 518.509489744, 524.912729158, 529.34264645, 531.968893772, 534.148706267, 537.806463336, 544.438644352, 554.327574427, 566.397348018, 578.75848892, 589.60461995, 597.959787247],
            [0.0, -7.32141345485, -2.24188910783, 17.5084796651, 51.6590699798, 93.8424214009, 135.343039126, 170.125201275, 197.650834121, 222.064242203, 248.607036376, 279.684062406, 313.008179335, 342.86219937, 363.538440045, 372.775003614, 373.161313251, 370.851530719, 372.474802633, 382.014525045, 399.353163007, 421.090926094, 442.910437059, 462.023619701, 478.326970062, 493.697177809, 510.152892538, 528.097862559, 545.745272605, 560.045411786, 568.473950932, 570.569080859, 568.33499032, 565.33599917, 565.04076393, 569.344280019, 578.025459773, 589.313541658, 601.112627727, 612.12330761, 622.251139581],
            [0.0, 54.678748393, 121.394668143, 208.452200799, 306.041391217, 398.631547269, 474.572074273, 531.509738911, 575.808019837, 617.144934365, 661.963552978, 709.764783047, 754.225183121, 788.111858531, 808.578183823, 819.578182348, 830.147077115, 849.814125848, 883.766967456, 930.492767664, 983.033799967, 1032.881029, 1074.15100701, 1105.82853721, 1130.99858244, 1153.94444886, 1177.10492734, 1199.68304728, 1218.61976736, 1231.12029697, 1236.99755707, 1239.38549692, 1243.46615139, 1253.99464153, 1273.03333799, 1299.12425782, 1328.24952, 1355.91927365, 1379.17434995, 1397.46336442, 1412.09464679],
            [0.0, -5.59381121367, -6.01373233059, 4.83142313275, 21.1739544878, 34.3051889838, 38.7010272789, 34.9542139634, 28.7051874574, 26.678395734, 32.3988547991, 44.1379563806, 56.1489085777, 62.2656860738, 59.5305824776, 49.7466949426, 38.2170435782, 30.6821712944, 30.2593496858, 36.10112787, 44.3695218216, 50.7468774712, 52.9104851442, 51.6039795728, 49.7539472059, 50.3745260466, 54.6119035707, 61.0520061819, 66.6359759505, 68.5333276796, 65.7881163256, 59.803115397, 53.4841227618, 49.631801088, 49.530809487, 52.4969466671, 56.5385444144, 59.6447247505, 60.9067856081, 60.8513420596, 60.8767306988],
            [0.0, 22.0593724245, 75.299753472, 143.661953912, 211.305666322, 267.236955059, 309.65906556, 344.998383794, 382.251688146, 426.37657477, 474.764060873, 518.758766256, 549.121274416, 561.882979157, 560.849999812, 555.762561579, 557.376420392, 572.345349449, 600.584890214, 636.385043607, 672.253051872, 703.049285576, 728.104467777, 750.423588028, 773.652221734, 799.064749965, 824.36425085, 844.938101487, 856.732471535, 858.871307351, 854.438182392, 849.109183702, 848.506992761, 855.738284181, 870.39422162, 889.395243477, 909.004535532, 926.767681048, 942.324017248, 956.802286135, 971.369078358],
            [0.0, 81.5258458452, 167.954544262, 251.942487611, 324.828230557, 385.701675362, 441.363469759, 500.691535249, 567.946147648, 639.329505724, 704.771359418, 753.728252526, 781.558412206, 792.373842757, 796.613314831, 805.836725536, 827.489063946, 862.171522477, 904.702218319, 948.012870008, 987.343532351, 1022.31040663, 1055.96195795, 1091.74822092, 1130.36036297, 1168.6445522, 1201.06165348, 1222.79807644, 1232.6461522, 1233.83971401, 1232.48418199, 1234.73797607, 1244.26462366, 1261.16105961, 1282.7716539, 1305.70525122, 1327.77001704, 1348.74905678, 1369.73822587, 1391.65112647, 1413.94124901],
        ])
        # This is copy & paste from the model answer as well
        assert_array_almost_equal(answer_lookup[Moment(np.array([1, 0, 0]), symbol=y_0)],
                                  answers[0])
        assert_array_almost_equal(answer_lookup[Moment(np.array([0, 1, 0]), symbol=y_1)],
                                  answers[1])
        assert_array_almost_equal(answer_lookup[Moment(np.array([0, 0, 1]), symbol=y_2)],
                                  answers[2])

        assert_array_almost_equal(answer_lookup[Moment(np.array([0, 0, 2]), symbol=yx1)],
                                  answers[3])

        assert_array_almost_equal(answer_lookup[Moment(np.array([0, 1, 1]), symbol=yx3)],
                                  answers[4])

        assert_array_almost_equal(answer_lookup[Moment(np.array([0, 2, 0]), symbol=yx5)],
                                  answers[5])
        assert_array_almost_equal(answer_lookup[Moment(np.array([1, 0, 1]), symbol=yx8)],
                                  answers[6])
        assert_array_almost_equal(answer_lookup[Moment(np.array([1, 1, 0]), symbol=yx10)],
                                  answers[7])
        assert_array_almost_equal(answer_lookup[Moment(np.array([2, 0, 0]), symbol=yx13)],
                                  answers[8])


    def test_p53_lna(self):
        # Again just an output of means.approximation.LinearNoiseApproximation(p53).run()

        c_0, c_1, c_2, c_3, c_4, c_5, c_6 = symbols(['c_0', 'c_1', 'c_2', 'c_3', 'c_4', 'c_5', 'c_6'])
        constants = [c_0, c_1, c_2, c_3, c_4, c_5, c_6]

        y_0, y_1, y_2 = symbols(['y_0', 'y_1', 'y_2'])

        V_0_0 = Symbol('V_0_0')
        V_0_2 = Symbol('V_0_2')
        V_2_0 = Symbol('V_2_0')
        V_0_1 = Symbol('V_0_1')
        V_2_1 = Symbol('V_2_1')
        V_2_2 = Symbol('V_2_2')
        V_1_0 = Symbol('V_1_0')
        V_1_2 = Symbol('V_1_2')
        V_1_1 = Symbol('V_1_1')

        left_hand_side_descriptors = [Moment(np.array([1, 0, 0]), symbol=y_0),
                         Moment(np.array([0, 1, 0]), symbol=y_1),
                         Moment(np.array([0, 0, 1]), symbol=y_2),
                         VarianceTerm((0, 0), V_0_0),
                         VarianceTerm((0, 1), V_0_1),
                         VarianceTerm((0, 2), V_0_2),
                         VarianceTerm((1, 0), V_1_0),
                         VarianceTerm((1, 1), V_1_1),
                         VarianceTerm((1, 2), V_1_2),
                         VarianceTerm((2, 0), V_2_0),
                         VarianceTerm((2, 1), V_2_1),
                         VarianceTerm((2, 2), V_2_2)]

        right_hand_side = MutableDenseMatrix([[c_0 - c_1*y_0 - c_2*y_0*y_2/(c_6 + y_0)], [c_3*y_0 - c_4*y_1], [c_4*y_1 - c_5*y_2], [2*V_0_0*(-c_1 + c_2*y_0*y_2/(c_6 + y_0)**2 - c_2*y_2/(c_6 + y_0)) - V_0_2*c_2*y_0/(c_6 + y_0) - V_2_0*c_2*y_0/(c_6 + y_0) + c_0**Float('1.0', prec=15) + (c_1*y_0)**Float('1.0', prec=15) + (c_2*y_0*y_2/(c_6 + y_0))**Float('1.0', prec=15)], [V_0_0*c_3 - V_0_1*c_4 + V_0_1*(-c_1 + c_2*y_0*y_2/(c_6 + y_0)**2 - c_2*y_2/(c_6 + y_0)) - V_2_1*c_2*y_0/(c_6 + y_0)], [V_0_1*c_4 - V_0_2*c_5 + V_0_2*(-c_1 + c_2*y_0*y_2/(c_6 + y_0)**2 - c_2*y_2/(c_6 + y_0)) - V_2_2*c_2*y_0/(c_6 + y_0)], [V_0_0*c_3 - V_1_0*c_4 + V_1_0*(-c_1 + c_2*y_0*y_2/(c_6 + y_0)**2 - c_2*y_2/(c_6 + y_0)) - V_1_2*c_2*y_0/(c_6 + y_0)], [V_0_1*c_3 + V_1_0*c_3 - 2*V_1_1*c_4 + (c_3*y_0)**Float('1.0', prec=15) + (c_4*y_1)**Float('1.0', prec=15)], [V_0_2*c_3 + V_1_1*c_4 - V_1_2*c_4 - V_1_2*c_5 - (c_4*y_1)**Float('1.0', prec=15)], [V_1_0*c_4 - V_2_0*c_5 + V_2_0*(-c_1 + c_2*y_0*y_2/(c_6 + y_0)**2 - c_2*y_2/(c_6 + y_0)) - V_2_2*c_2*y_0/(c_6 + y_0)], [V_1_1*c_4 + V_2_0*c_3 - V_2_1*c_4 - V_2_1*c_5 - (c_4*y_1)**Float('1.0', prec=15)], [V_1_2*c_4 + V_2_1*c_4 - 2*V_2_2*c_5 + (c_4*y_1)**Float('1.0', prec=15) + (c_5*y_2)**Float('1.0', prec=15)]])

        problem = ODEProblem('LNA', left_hand_side_descriptors, right_hand_side, constants)

        simulation = Simulation(problem, rtol=1e-4, atol=1e-4)

        timepoints = np.arange(0, 20.5, 0.5)
        parameters = [90, 0.002, 1.2, 1.1, 0.8, 0.96, 0.01]
        initial_conditions = [80, 40, 60]

        results = simulation.simulate_system(parameters, initial_conditions, timepoints)

        results_dict = {t.description: t.values for t in results}

        answers = np.array([
            [80., 91.26097381, 102.686108, 109.93308216, 110.94858087, 105.34987029, 94.05328135, 78.9239411, 62.38543885, 46.99878992, 35.05376129, 28.2244299, 27.33661061, 32.27677149, 42.05058041, 54.97059891, 68.94003811, 81.78861543, 91.60613728, 97.0227379, 97.39528817, 92.87537891, 84.35347704, 73.29285155, 61.48309574, 50.75405963, 42.69531417, 38.42364318, 38.4323354, 42.54232897, 49.95794698, 59.41351719, 69.3851293, 78.3331611, 84.93735207, 88.28883079, 88.01157972, 84.29672107, 77.85013689, 69.77195431, 61.36087086],
            [40., 65.67715304, 88.25188557, 107.66704834, 122.50241615, 131.29590318, 133.21994739, 128.3786053, 117.83756996, 103.45866264, 87.60084346, 72.74525601, 61.11454583, 54.34677538, 53.27047906, 57.81369043, 67.05224621, 79.38539246, 92.80735321, 105.22934245, 114.80107159, 120.18268515, 120.72775581, 116.55314189, 108.48971409, 97.92636093, 86.57538872, 76.19823657, 68.3349541, 64.07872927, 63.92813211, 67.73608625, 74.75901848, 83.79464827, 93.38392496, 102.04375762, 108.49383618, 111.84225053, 111.70451252, 108.25010787, 102.14491466],
            [60., 54.3420914, 58.43317844, 67.62291484, 78.7345431, 89.31893624, 97.49379049, 101.98716197, 102.21209016, 98.28658491, 90.97026836, 81.51375198, 71.44388417, 62.31900523, 55.48902827, 51.89854087, 51.95994857, 55.51268372, 61.87133408, 69.95162198, 78.45193231, 86.06047015, 91.65543006, 94.4679905, 94.18483536, 90.97707859, 85.454211, 78.55315126, 71.38195571, 65.04389383, 60.46959542, 58.28254614, 58.71694545, 61.59818504, 66.38633414, 72.27343211, 78.31757247, 83.59156502, 87.32273779, 89.00744549, 88.47562941]
        ])



        assert_array_almost_equal(results_dict[Moment(np.array([1, 0, 0]), symbol=y_0)],
                                  answers[0])

        assert_array_almost_equal(results_dict[Moment(np.array([0, 1, 0]), symbol=y_1)],
                                  answers[1])

        assert_array_almost_equal(results_dict[Moment(np.array([0, 0, 1]), symbol=y_2)],
                                  answers[2])

    def test_MM_3_moments(self):

        c_0, c_1, c_2 = symbols(['c_0', 'c_1', 'c_2'])
        constants = [c_0, c_1, c_2]

        y_0, y_1 = symbols(['y_0', 'y_1'])

        yx1 = Symbol('yx1')
        yx2 = Symbol('yx2')
        yx3 = Symbol('yx3')
        yx4 = Symbol('yx4')
        yx5 = Symbol('yx5')
        yx6 = Symbol('yx6')
        yx7 = Symbol('yx7')

        right_hand_side = MutableDenseMatrix([[-c_0*y_0*(y_0 + y_1 - 181) - c_0*yx3 - c_0*yx5 - c_1*(y_0 + y_1 - 301)], [c_2*(-y_0 - y_1 + 301)], [c_2*(-y_0 - y_1 - 2*yx1 - 2*yx3 + 301)], [c_2*(-y_0 - y_1 - 3*yx1 - 3*yx2 - 3*yx3 - 3*yx4 + 301)], [-c_0*yx4 - c_0*yx6 - c_2*yx5 - yx1*(c_0*y_0 + c_1) - yx3*(2*c_0*y_0 + c_0*y_1 - 181*c_0 + c_1 + c_2)], [-c_0*y_0*yx2 - 2*c_0*y_0*yx4 - c_0*y_1*yx4 + c_0*yx1*yx3 + c_0*yx1*yx5 + 181*c_0*yx4 - c_1*yx2 - c_1*yx4 - c_2*yx3 - 2*c_2*yx4 - c_2*yx5 - 2*c_2*yx6], [c_0*y_0**2 + c_0*y_0*y_1 - 181*c_0*y_0 - 2*c_0*yx6 - 2*c_0*yx7 - c_1*y_0 - c_1*y_1 + 301*c_1 - yx3*(2*c_0*y_0 - c_0 + 2*c_1) - yx5*(4*c_0*y_0 + 2*c_0*y_1 - 363*c_0 + 2*c_1)], [c_0*y_0*yx1 + 2*c_0*y_0*yx3 - 2*c_0*y_0*yx4 - 4*c_0*y_0*yx6 + c_0*y_1*yx3 - 2*c_0*y_1*yx6 + 2*c_0*yx3**2 + 2*c_0*yx3*yx5 - 181*c_0*yx3 + c_0*yx4 + 363*c_0*yx6 - c_1*yx1 - c_1*yx3 - 2*c_1*yx4 - 2*c_1*yx6 - c_2*yx6 - c_2*yx7], [-c_0*y_0**2 - c_0*y_0*y_1 + 3*c_0*y_0*yx3 + 6*c_0*y_0*yx5 - 3*c_0*y_0*yx6 - 6*c_0*y_0*yx7 + 181*c_0*y_0 + 3*c_0*y_1*yx5 - 3*c_0*y_1*yx7 + 3*c_0*yx3*yx5 - c_0*yx3 + 3*c_0*yx5**2 - 544*c_0*yx5 + 3*c_0*yx6 + 546*c_0*yx7 - c_1*y_0 - c_1*y_1 - 3*c_1*yx3 - 3*c_1*yx5 - 3*c_1*yx6 - 3*c_1*yx7 + 301*c_1]])

        left_hand_side_descriptors = [Moment(np.array([1, 0]), symbol=y_0),
                         Moment(np.array([0, 1]), symbol=y_1),
                         Moment(np.array([0, 2]), symbol=yx1),
                         Moment(np.array([0, 3]), symbol=yx2),
                         Moment(np.array([1, 1]), symbol=yx3),
                         Moment(np.array([1, 2]), symbol=yx4),
                         Moment(np.array([2, 0]), symbol=yx5),
                         Moment(np.array([2, 1]), symbol=yx6),
                         Moment(np.array([3, 0]), symbol=yx7)]

        problem = ODEProblem('MEA', left_hand_side_descriptors, right_hand_side, constants)

        parameters = [0.00166, 0.001, 0.1]
        initial_conditions = [301, 0, 0, 0, 0]
        timepoints = np.arange(0, 51, 1)

        sim = Simulation(problem, rtol=1e-4, atol=1e-4)
        results = sim.simulate_system(parameters, initial_conditions, timepoints)
        results_dict = {t.description: t.values for t in results}

        answers = np.array([
            [301.0, 256.492639782, 229.852002298, 211.465246643, 197.360680462, 185.656067167, 175.380946164, 166.006967909, 157.236063077, 148.896347433, 140.88846739, 133.153986764, 125.659439703, 118.386845837, 111.3278231, 104.479371328, 97.8417753998, 91.4179868074, 85.2122859482, 79.2299290872, 73.4762649572, 67.9561629325, 62.6740800899, 57.6343280823, 52.8406445593, 48.2960456304, 44.0024086727, 39.9603504911, 36.16930043, 32.6274667775, 29.3318107918, 26.2780023115, 23.4603636677, 20.8719439867, 18.5045767987, 16.3490470065, 14.395249091, 12.6323324801, 11.0487992245, 9.63274648875, 8.37203895862, 7.25450475517, 6.26807979261, 5.40095720097, 4.64172176857, 3.97948861823, 3.40398871014, 2.90558194914, 2.47536220203, 2.10518099895, 1.78758137424],
            [0.0, 2.36149153969, 7.7515135209, 14.7191363234, 22.5457124691, 30.843296667, 39.3904369603, 48.0553556601, 56.7567883911, 65.4428704627, 74.0793950352, 82.642554975, 91.115014262, 99.4835099842, 107.737368719, 115.867400091, 123.865264401, 131.723319094, 139.434356781, 146.991380154, 154.3876025, 161.61631605, 168.670979419, 175.545274097, 182.233112456, 188.72866768, 195.026441874, 201.121335459, 207.008736955, 212.684566262, 218.145373121, 223.388395517, 228.41161221, 233.213793267, 237.794535739, 242.154315467, 246.294483432, 250.217259442, 253.925718666, 257.42376128, 260.716059186, 263.807993051, 266.705591313, 269.415454603, 271.944650037, 274.300633231, 276.49114698, 278.52417699, 280.407807446, 282.150165574, 283.759345221],
            [0.0, 2.31983366694, 7.35677890779, 13.4369006791, 19.7921073564, 26.0713369383, 32.1172763867, 37.8624270442, 43.2798014597, 48.3595432404, 53.0981064354, 57.4931041976, 61.5416214957, 65.2396982683, 68.5823780045, 71.5640488513, 74.1790402195, 76.4219370815, 78.2880507847, 79.7739392558, 80.877692597, 81.5994678948, 81.9418622248, 81.9101165813, 81.5123887702, 80.759850581, 79.6669760185, 78.2515027695, 76.53436158, 74.5395377731, 72.2938329853, 69.8264289538, 67.1684025552, 64.3521945724, 61.4111404207, 58.3785704494, 55.2872553061, 52.1687096759, 49.05287029, 45.9672363218, 42.9365686348, 39.9826065782, 37.1239500822, 34.375882259, 31.7503773586, 29.2562703437, 26.8995172184, 24.6833366057, 22.6086606926, 20.6744053803, 18.8777925297],
            [0.0, -1.60651977695, -4.35451333791, -7.53161577455, -11.0191210379, -14.7162559649, -18.5146472936, -22.3127366438, -26.0237579598, -29.5773455771, -32.9180927464, -36.003062146, -38.7991769491, -41.2812403259, -43.430500085, -45.2333955826, -46.6807058177, -47.76736494, -48.492163277, -48.8578908996, -48.8710674558, -48.5419414176, -47.8846672589, -46.9174248043, -45.6622315935, -44.144796867, -42.3941272524, -40.4420316821, -38.3225372206, -36.0714116071, -33.7252518691, -31.3205528372, -28.8928157273, -26.4757553941, -24.1006521763, -21.7952959881, -19.5836603501, -17.4854768187, -15.5161653293, -13.6865606347, -12.0032532766, -10.4689667117, -9.08303920281, -7.84166718144, -6.73831476688, -5.76491066546, -4.9123028337, -4.17038178537, -3.52880822979, -2.97706079856, -2.50492476685],
            [0.0, 25.0309972905, 26.9056189306, 25.9215014325, 25.4621542384, 25.9865944764, 27.3412285302, 29.2665516824, 31.5222409808, 33.9145569056, 36.2960668935, 38.5579191108, 40.6207809933, 42.427986939, 43.9403899104, 45.1317260122, 45.9852160625, 46.4926493502, 46.6529136317, 46.4712781729, 45.9584959302, 45.1299930946, 44.0059191931, 42.6110459185, 40.9739861549, 39.126917131, 37.1045881709, 34.9436988956, 32.6818886916, 30.3570004948, 28.0057794184, 25.6628515305, 23.3600838559, 21.1259505297, 18.9849799989, 16.9569820825, 15.0569175729, 13.2950369601, 11.6771433347, 10.2050435322, 8.87723371848, 7.68932214367, 6.63447815273, 5.70399484066, 4.88806056883, 4.17686862218, 3.56031798898, 3.02810628792, 2.57009693759, 2.17743647448, 1.84217909453],
        ])

        assert_array_almost_equal(results_dict[Moment(np.array([1, 0]), symbol=y_0)], answers[0])
        assert_array_almost_equal(results_dict[Moment(np.array([0, 1]), symbol=y_1)], answers[1])
        assert_array_almost_equal(results_dict[Moment(np.array([0, 2]), symbol=yx1)], answers[2])
        assert_array_almost_equal(results_dict[Moment(np.array([1, 1]), symbol=yx3)], answers[3])
        assert_array_almost_equal(results_dict[Moment(np.array([2, 0]), symbol=yx5)], answers[4])

    def test_mm_lna(self):

        c_0 = Symbol('c_0')
        c_1 = Symbol('c_1')
        c_2 = Symbol('c_2')

        constants = [c_0, c_1, c_2]

        y_0 = Symbol('y_0')
        y_1 = Symbol('y_1')

        V_0_0 = Symbol('V_0_0')
        V_0_1 = Symbol('V_0_1')
        V_1_0 = Symbol('V_1_0')
        V_1_1 = Symbol('V_1_1')

        right_hand_side = MutableDenseMatrix([[-c_0*y_0*(y_0 + y_1 - 181) + c_1*(-y_0 - y_1 + 301)], [c_2*(-y_0 - y_1 + 301)], [2*V_0_0*(-c_0*y_0 - c_0*(y_0 + y_1 - 181) - c_1) + V_0_1*(-c_0*y_0 - c_1) + V_1_0*(-c_0*y_0 - c_1) + (c_1*(-y_0 - y_1 + 301))**Float('1.0', prec=15) + (c_0*y_0*(y_0 + y_1 - 181))**Float('1.0', prec=15)], [-V_0_0*c_2 - V_0_1*c_2 + V_0_1*(-c_0*y_0 - c_0*(y_0 + y_1 - 181) - c_1) + V_1_1*(-c_0*y_0 - c_1)], [-V_0_0*c_2 - V_1_0*c_2 + V_1_0*(-c_0*y_0 - c_0*(y_0 + y_1 - 181) - c_1) + V_1_1*(-c_0*y_0 - c_1)], [-V_0_1*c_2 - V_1_0*c_2 - 2*V_1_1*c_2 + (c_2*(-y_0 - y_1 + 301))**Float('1.0', prec=15)]])

        left_hand_side_descriptors = [Moment(np.array([1, 0]), symbol=y_0),
                         Moment(np.array([0, 1]), symbol=y_1),
                         VarianceTerm((0, 0), V_0_0),
                         VarianceTerm((0, 1), V_0_1),
                         VarianceTerm((1, 0), V_1_0),
                         VarianceTerm((1, 1), V_1_1)]

        problem = ODEProblem('LNA', left_hand_side_descriptors, right_hand_side, constants)

        simulation = Simulation(problem, rtol=1e-4, atol=1e-4)

        parameters = [0.00166, 0.001, 0.1]
        initial_conditions = [301, 0, 0, 0, 0]
        timepoints = np.arange(0, 51, 1)

        results = simulation.simulate_system(parameters, initial_conditions, timepoints)
        results_dict = {t.description: t.values for t in results}

        answers = np.array([
            [301., 256.51498559, 229.89542064, 211.52116974, 197.42316884, 185.71830873, 175.44246068, 166.06820577, 157.29328021, 148.95026194, 140.94583069, 133.21595844, 125.71905663, 118.4410609, 111.37967251, 104.52979537, 97.88831544, 91.45915339, 85.24949606, 79.26364987, 73.50479093, 67.97826296, 62.69042542, 57.64565314, 52.84654527, 48.29608775, 43.99643525, 39.94831679, 36.15119384, 32.60369428, 29.30290506, 26.24448926, 23.42270704, 20.83070314, 18.46055884, 16.30306856, 14.34802762, 12.58444992, 11.00100171, 9.58569265, 8.32629168, 7.2105353, 6.22630953, 5.3616935, 4.6051838, 3.94581727, 3.3733408, 2.87793087, 2.45062139, 2.08319264, 1.76820452],
            [0., 2.36069323, 7.74739569, 14.71042288, 22.53210695, 30.82462962, 39.36700012, 48.02794222, 56.72574442, 65.40823306, 74.04120501, 82.60138629, 91.07160645, 99.4387013, 107.69175142, 115.82124162, 123.81890377, 131.67725313, 139.38904945, 146.9471517, 154.34469731, 161.57508413, 168.63182448, 175.50852451, 182.19903659, 188.69753948, 194.99856707, 201.09704246, 206.9883868, 212.668393, 218.13351417, 223.38092476, 228.40860251, 233.21525316, 237.80031763, 242.16422414, 246.30828444, 250.23479944, 253.94661212, 257.44759737, 260.74242851, 263.83654326, 266.73591384, 269.44707387, 271.97713666, 274.33359706, 276.52427151, 278.55708094, 280.44017531, 282.18173647, 283.78989916]
        ])


        assert_array_almost_equal(results_dict[Moment(np.array([1, 0]), symbol=y_0)], answers[0])
        assert_array_almost_equal(results_dict[Moment(np.array([0, 1]), symbol=y_1)], answers[1])

