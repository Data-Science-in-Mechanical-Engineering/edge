from numpy import atleast_1d

from .environments import Environment
from edge.dynamics import HovershipDynamics, DiscreteHovershipDynamics
from edge.space import Box, Discrete, StateActionSpace
from edge.reward import ConstantReward


class Hovership(Environment):
    def __init__(self, random_start=False, default_initial_state=None,
                 dynamics_parameters=None, reward=None,
                 reward_done_threshold=None, steps_done_threshold=None,
                 goal_state=False):
        if dynamics_parameters is None:
            dynamics_parameters = {}
        default_dynamics_parameters = {
            'ground_gravity': 0.1,
            'gravity_gradient': 1,
            'control_frequency': 1,
            'max_thrust': 0.8,
            'max_altitude': 2,
            'shape': (200, 150)
        }
        default_dynamics_parameters.update(dynamics_parameters)
        dynamics = HovershipDynamics(**default_dynamics_parameters)

        if reward is None:
            # The default reward gives a 1 reward when the agent is above 80% of the ceiling value
            max_altitude = default_dynamics_parameters['max_altitude']
            max_thrust = default_dynamics_parameters['max_thrust']
            rewarded_set = StateActionSpace.from_product(
                Box([0.8 * max_altitude, 0],
                    [max_altitude, max_thrust],
                    (100, 100)
                    )
            )
            reward = ConstantReward(
                dynamics.stateaction_space,
                constant=1,
                rewarded_set=rewarded_set
            )

        if default_initial_state is None:
            # The default initial state is unrewarded with the default reward
            max_altitude = default_dynamics_parameters['max_altitude']
            default_initial_state = atleast_1d(0.75 * max_altitude)

        super(Hovership, self).__init__(
            dynamics=dynamics,
            reward=reward,
            default_initial_state=default_initial_state,
            random_start=random_start,
            reward_done_threshold=reward_done_threshold,
            steps_done_threshold=steps_done_threshold
        )

        self.goal_state = goal_state

    def is_failure_state(self, state):
        return state[0] == 0

    @property
    def done(self):
        return (self.goal_state and self.s[0] == 2.) or super().done


class DiscreteHovership(Environment):
    def __init__(self, random_start=False, default_initial_state=None,
                 dynamics_parameters=None, reward=None,
                 reward_done_threshold=None, steps_done_threshold=None):
        if dynamics_parameters is None:
            dynamics_parameters = {}
        default_dynamics_parameters = {
            'ground_gravity': 1,
            'gravity_gradient': 1,
            'max_thrust': 5,
            'max_altitude': 10,
            'minimum_gravity_altitude': 9,
            'maximum_gravity_altitude': 3
        }
        default_dynamics_parameters.update(dynamics_parameters)
        dynamics = DiscreteHovershipDynamics(**default_dynamics_parameters)

        if reward is None:
            # The default reward is simply getting to the top
            max_altitude = default_dynamics_parameters['max_altitude']
            max_thrust = default_dynamics_parameters['max_thrust']
            rewarded_set = StateActionSpace(
                Discrete(n=1, start=max_altitude, end=max_altitude),
                Discrete(max_thrust + 1)
            )
            reward = ConstantReward(
                dynamics.stateaction_space,
                constant=1,
                rewarded_set=rewarded_set
            )

        if default_initial_state is None:
            max_altitude = default_dynamics_parameters['max_altitude']
            default_initial_state = atleast_1d(max_altitude)

        super(DiscreteHovership, self).__init__(
            dynamics=dynamics,
            reward=reward,
            default_initial_state=default_initial_state,
            random_start=random_start,
            reward_done_threshold=reward_done_threshold,
            steps_done_threshold=steps_done_threshold
        )

    def is_failure_state(self, state):
        # Remember that states are np.ndarray
        return state[0] == 0
