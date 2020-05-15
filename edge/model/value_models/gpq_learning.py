import numpy as np

from .. import GPModel
from ..inference import MaternGP


class GPQLearning(GPModel):
    def __init__(self, env, step_size, discount_rate,
                 x_seed, y_seed, gp_params=None):
        if gp_params is None:
            gp_params = {}

        gp = MaternGP(x_seed, y_seed, **gp_params)
        super(GPQLearning, self).__init__(env, gp)
        self.step_size = step_size
        self.discount_rate = discount_rate

    def update(self, state, action, new_state, reward):
        q_value_step = self.step_size * (
            reward + self.discount_rate * np.max(self[new_state, :])
        )
        q_value_update = self[state, action] + q_value_step

        stateaction = self.env.stateaction_space[state, action]
        self.gp = self.gp.append_data(stateaction, q_value_update)
