from means.io.serialise import SerialisableObject
from means.util.decorators import memoised_property

class ConvergenceStatusBase(SerialisableObject):

    def __init__(self, convergence_achieved):
        self.__convergence_achieved = convergence_achieved

    @property
    def convergence_achieved(self):
        return self.__convergence_achieved

    @property
    def _convergence_achieved_str(self):
        return 'convergence achieved' if self.convergence_achieved else 'convergence not achieved'

    def __unicode__(self):
        return u"<Inference {self._convergence_achieved_str}>".format(self=self)

    def __str__(self):
        return unicode(self).encode("utf8")

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.convergence_achieved == other.convergence_achieved

class NormalConvergenceStatus(ConvergenceStatusBase):

    yaml_tag = '!convergence-status'

    def __init__(self, warn_flag, iterations_taken, function_calls_made):
        convergence_achieved = warn_flag != 1 and warn_flag != 2
        super(NormalConvergenceStatus, self).__init__(convergence_achieved)

        self.__iterations_taken = iterations_taken
        self.__function_calls_made = function_calls_made
        self.__warn_flag = warn_flag

    @property
    def iterations_taken(self):
        return self.__iterations_taken

    @property
    def function_calls_made(self):
        return self.__function_calls_made

    @property
    def warn_flag(self):
        return self.__warn_flag

    def __unicode__(self):
        return u"<Inference {self._convergence_achieved_str} " \
               u"in {self.iterations_taken} iterations " \
               u"and {self.function_calls_made} function calls>".format(self=self)

    @classmethod
    def to_yaml(cls, dumper, data):
        mapping = [('warn_flag', data.warn_flag),
                   ('iterations_taken', data.iterations_taken),
                   ('function_calls_made', data.function_calls_made)]
        return dumper.represent_mapping(cls.yaml_tag, mapping)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return super(NormalConvergenceStatus, self).__eq__(other) \
            and self.iterations_taken == other.iterations_taken\
            and self.function_calls_made == other.function_calls_made \
            and self.warn_flag == other.warn_flag


class SolverErrorConvergenceStatus(ConvergenceStatusBase):

    yaml_tag = '!multiple-solver-errors'

    def __init__(self):
        super(SolverErrorConvergenceStatus, self).__init__(False)

    def __unicode__(self):
        return u"<Inference {self._convergence_achieved_str} " \
               u"as it was cancelled after maximum number of solver errors occurred.".format(self=self)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_mapping(cls.yaml_tag, {})


    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return super(SolverErrorConvergenceStatus, self).__eq__(other)

class InferenceResultsCollection(SerialisableObject):
    __inference_results = None

    yaml_tag = '!serialisable-results-collection'

    def __init__(self, inference_results):
        self.__inference_results = sorted(inference_results, key=lambda x: x.distance_at_minimum)

    @classmethod
    def to_yaml(cls, dumper, data):
        sequence = data.results
        return dumper.represent_sequence(cls.yaml_tag, sequence)

    @classmethod
    def from_yaml(cls, loader, node):
        sequence = loader.construct_sequence(node, deep=True)
        return cls(sequence)

    @property
    def results(self):
        """

        :return: The results of performed inferences
        :rtype: list[:class:`InferenceResult`]
        """
        return self.__inference_results

    def __iter__(self):
        return iter(self.results)

    def __len__(self):
        return len(self.results)

    def __getitem__(self, item):
        return self.results[item]

    @property
    def number_of_results(self):
        return len(self.results)

    @property
    def best(self):
        return self.__inference_results[0]

    def __unicode__(self):
        return u"""
        {self.__class__!r}

        Number of inference results in collection: {self.number_of_results}
        Best:
        {self.best!r}
        """.format(self=self)

    def __str__(self):
        return unicode(self).encode("utf8")

    def __repr__(self):
        return str(self)


    def plot(self):
        from matplotlib import pyplot as plt

        trajectory_descriptions = [x.description for x in self.results[0].starting_trajectories]


        # Plot in reverse order so the best one is always on top
        reversed_results = list(reversed(self.results))
        # Plot all but last one (as the alpha will change)

        # Let's make worse results fade
        alpha = 0.2

        for description in trajectory_descriptions:
            plt.figure()
            plt.title(description)
            f = lambda trajectory: trajectory.description == description
            first = True
            for result in reversed_results[:-1]:
                if first:
                    label_starting = 'Alternative Starting Trajectories'
                    label_optimal = 'Alternative Optimised Trajectories'
                    first = False
                else:
                    label_starting = ''
                    label_optimal = ''

                result.plot(filter_plots_function=f,
                            legend=False, kwargs_starting_trajectories={'alpha': alpha, 'label': label_starting},
                            kwargs_optimal_trajectories={'alpha': alpha, 'label': label_optimal},
                            # Do not draw observed data, it is the same for all
                            kwargs_observed_data={'label': '', 'alpha': 0},
                            plot_intermediate_solutions=False)

            self.best.plot(filter_plots_function=f, plot_intermediate_solutions=False,
                           kwargs_starting_trajectories={'label': 'Best Starting Trajectory'},
                           kwargs_optimal_trajectories={'label': 'Best Optimised Trajectory'})


class InferenceResult(SerialisableObject):

    __inference = None

    __optimal_parameters = None
    __optimal_initial_conditions = None

    __distance_at_minimum = None
    __iterations_taken = None
    __function_calls_made = None
    __warning_flag = None
    __solutions = None

    yaml_tag = '!inference-result'

    def __init__(self, inference,
                 optimal_parameters, optimal_initial_conditions, distance_at_minimum, convergence_status,
                 solutions):

        """

        :param inference:
        :param optimal_parameters:
        :param optimal_initial_conditions:
        :param distance_at_minimum:
        :param convergence_status:
        :type convergence_status: :class:`ConvergenceStatusBase`
        :param solutions:
        """
        self.__inference = inference
        self.__optimal_parameters = optimal_parameters
        self.__optimal_initial_conditions = optimal_initial_conditions
        self.__distance_at_minimum = distance_at_minimum
        self.__convergence_status = convergence_status
        self.__solutions = solutions

    @property
    def inference(self):
        return self.__inference

    @property
    def problem(self):
        return self.inference.problem


    @property
    def observed_trajectories(self):
        return self.inference.observed_trajectories

    @property
    def starting_parameters(self):
        return self.inference.starting_parameters

    @property
    def starting_initial_conditions(self):
        return self.inference.starting_conditions

    @property
    def optimal_parameters(self):
        return self.__optimal_parameters

    @property
    def optimal_initial_conditions(self):
        return self.__optimal_initial_conditions

    @property
    def distance_at_minimum(self):
        return self.__distance_at_minimum

    @property
    def convergence_status(self):
        return self.__convergence_status

    @property
    def solutions(self):
        """
        Solutions at each each iteration of optimisation.
        :return: a list of (parameters, conditions) pairs
        :rtype: list[tuple]|None
        """
        return self.__solutions

    @memoised_property
    def starting_trajectories(self):
        timepoints = self.observed_trajectories[0].timepoints

        try:
            starting_trajectories = self.inference.simulation.simulate_system(self.starting_parameters,
                                                                     self.starting_initial_conditions, timepoints)
        # TODO: change exception type
        except Exception as e:
            print 'Warning: got {0!r} when obtaining starting trajectories, they will not be plotted'.format(e)
            return []

        return starting_trajectories

    @memoised_property
    def optimal_trajectories(self):
        timepoints = self.observed_trajectories[0].timepoints
        try:
            optimal_trajectories = self.inference.simulation.simulate_system(self.optimal_parameters,
                                                                    self.optimal_initial_conditions, timepoints)
        except Exception as e:
            print 'Warning: got {0!r} when obtaining optimal trajectories, they will not be plotted'.format(e)
            return []

        return optimal_trajectories

    @memoised_property
    def intermediate_trajectories(self):
        if self.solutions is None:
            return []

        timepoints = self.observed_trajectories[0].timepoints
        simulation = self.inference.simulation
        trajectories_collection = []

        for parameters, initial_conditions in self.solutions:
            try:
                trajectories_collection.append(simulation.simulate_system(parameters, initial_conditions, timepoints))
            except Exception as e:
                print "Warning: got {0!r} when trying to obtain one of the intermediate trajectories. " \
                      "It will not be plotted".format(e)
                continue

        return trajectories_collection

    def plot(self, plot_intermediate_solutions=True,
             plot_observed_data=True, plot_starting_trajectory=True, plot_optimal_trajectory=True,
             filter_plots_function=None, legend=True,
             kwargs_observed_data=None, kwargs_starting_trajectories=None, kwargs_optimal_trajectories=None,
             kwargs_intermediate_trajectories=None):
        """
        Plot the inference result.

        :param plot_intermediate_solutions: plot the trajectories resulting from the intermediate solutions as well
        :param filter_plots_function: A function that takes a trajectory object and returns True if it should be
                                      plotted and false if not. None plots all available trajectories
        :param legend: Whether to draw the legend or not
        :param kwargs_observed_data: Kwargs to be passed to the ``trajectory.plot`` function for the observed data
        :param kwargs_starting_trajectories: kwargs to be passed to the ``trajectory.plot`` function for the starting
                                             trajectories
        :param kwargs_optimal_trajectories: kwargs to be passed to the ``trajectory.plot`` function for the optimal
                                            trajectories
        :param kwargs_intermediate_trajectories: kwargs to be passed to the ``trajectory.plot`` function for the
                                            intermediate trajectories
        """
        from matplotlib import pyplot as plt
        if filter_plots_function is None:
            filter_plots_function = lambda x: True

        observed_trajectories = self.observed_trajectories

        starting_trajectories = self.starting_trajectories
        optimal_trajectories = self.optimal_trajectories

        if plot_intermediate_solutions:
            intermediate_trajectories_list = self.intermediate_trajectories
        else:
            intermediate_trajectories_list = []

        def initialise_default_kwargs(kwargs, default_data):
            if kwargs is None:
                kwargs = {}

            for key, value in default_data.iteritems():
                if key not in kwargs:
                    kwargs[key] = value

            return kwargs

        trajectories_by_description = {}
        kwargs_observed_data = initialise_default_kwargs(kwargs_observed_data, {'label': "Observed data", 'marker': '+',
                                                                                'color': 'black', 'linestyle': 'None'})

        kwargs_optimal_trajectories = initialise_default_kwargs(kwargs_optimal_trajectories,
                                                                {'label': "Optimised Trajectory", 'color': 'blue'})

        kwargs_starting_trajectories = initialise_default_kwargs(kwargs_starting_trajectories,
                                                                 {'label': "Starting trajectory", 'color': 'green'})

        kwargs_intermediate_trajectories = initialise_default_kwargs(kwargs_intermediate_trajectories,
                                                                     {'label': 'Intermediate Trajectories',
                                                                      'alpha': 0.1, 'color': 'cyan'}
                                                                     )

        if plot_observed_data:
            for trajectory in observed_trajectories:
                if not filter_plots_function(trajectory):
                    continue

                try:
                    list_ = trajectories_by_description[trajectory.description]
                except KeyError:
                    list_ = []
                    trajectories_by_description[trajectory.description] = list_

                list_.append((trajectory, kwargs_observed_data))

        if plot_starting_trajectory:
            for trajectory in starting_trajectories:
                if not filter_plots_function(trajectory):
                    continue

                try:
                    list_ = trajectories_by_description[trajectory.description]
                except KeyError:
                    list_ = []
                    trajectories_by_description[trajectory.description] = list_

                list_.append((trajectory, kwargs_starting_trajectories))

        seen_intermediate_trajectories = set()
        for i, intermediate_trajectories in enumerate(intermediate_trajectories_list):
            for trajectory in intermediate_trajectories:
                if not filter_plots_function(trajectory):
                    continue

                seen = trajectory.description in seen_intermediate_trajectories
                kwargs = kwargs_intermediate_trajectories.copy()
                # Only set label once
                if not seen:
                    seen_intermediate_trajectories.add(trajectory.description)
                else:
                    kwargs['label'] = ''

                try:
                    list_ = trajectories_by_description[trajectory.description]
                except KeyError:
                    list_ = []

                trajectories_by_description[trajectory.description] = list_
                list_.append((trajectory, kwargs))

        if plot_optimal_trajectory:
            for trajectory in optimal_trajectories:
                if not filter_plots_function(trajectory):
                    continue

                try:
                    list_ = trajectories_by_description[trajectory.description]
                except KeyError:
                    list_ = []
                    trajectories_by_description[trajectory.description] = list_

                list_.append((trajectory, kwargs_optimal_trajectories))

        for description, trajectories_list in trajectories_by_description.iteritems():
            if len(trajectories_by_description) > 1:
                plt.figure()
            plt.title(description)

            for trajectory, kwargs in trajectories_list:
                trajectory.plot(**kwargs)

            if legend:
                plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)


    def __unicode__(self):
        return u"""
        {self.__class__!r}
        Starting Parameters: {self.starting_parameters!r}
        Optimal Parameters: {self.optimal_parameters!r}

        Starting Initial Conditions: {self.starting_initial_conditions!r}
        Optimal Initial Conditions: {self.optimal_initial_conditions!r}

        Distance at Minimum: {self.distance_at_minimum!r}
        Convergence status: {self.convergence_status!r}
        """.format(self=self)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return unicode(self).encode('utf8')

    @classmethod
    def to_yaml(cls, dumper, data):

        mapping = [('inference', data.inference),
                   ('optimal_parameters', data.optimal_parameters),
                   ('optimal_initial_conditions', data.optimal_initial_conditions),
                   ('distance_at_minimum', data.distance_at_minimum),
                   ('convergence_status', data.convergence_status),
                   ('solutions', data.solutions)]

        return dumper.represent_mapping(cls.yaml_tag, mapping)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.inference == other.inference \
            and self.optimal_parameters == other.optimal_parameters \
            and self.optimal_initial_conditions == other.optimal_initial_conditions \
            and self.distance_at_minimum == other.distance_at_minimum \
            and self.convergence_status == other.convergence_status \
            and self.solutions == other.solutions \