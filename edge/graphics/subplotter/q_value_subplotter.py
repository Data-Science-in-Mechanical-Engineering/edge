from numpy import squeeze, around, linspace, meshgrid, dstack
from scipy.interpolate import RegularGridInterpolator
import matplotlib as mpl

from . import Subplotter


class QValueSubplotter(Subplotter):
    def __init__(self, agent, colors, write_values=False, vmin=None, vmax=None,
                 scale='log'):
        super(QValueSubplotter, self).__init__(colors)
        self.agent = agent
        self.states = squeeze(self.model.env.state_space[:])
        self.actions = squeeze(self.model.env.action_space[:])
        stateaction_grid = self.model.env.stateaction_space[:, :]
        self.states_grid = stateaction_grid[:, :, 0]
        self.actions_grid = stateaction_grid[:, :, 1]
        self.write_values = write_values
        self.vmin = vmin
        self.vmax = vmax
        self.scale = scale

    @property
    def model(self):
        return self.agent.Q_model

    def __get_min_max(self, Q_values):
        if (self.vmin is not None) and (self.vmax is not None):
            qmin = self.vmin
            qmax = self.vmax
        else:
            nonzero_Q = Q_values[Q_values.nonzero()]
            if len(nonzero_Q) == 0:
                return -1, 1
            else:
                qmin = nonzero_Q.min()
                qmax = nonzero_Q.max()
                return qmin, qmax
        return qmin, qmax

    def draw_on_axs(self, ax_Q, Q_values):
        vmin, vmax = self.__get_min_max(Q_values)
        self.colors.q_values_norm = mpl.colors.SymLogNorm(
            linthresh=0.1, linscale=1, base=10, vmin=vmin, vmax=vmax
        ) if self.scale == 'log' else None
        image = ax_Q.pcolormesh(
            self.actions_grid,
            self.states_grid,
            Q_values,
            cmap=self.colors.cmap_q_values,
            norm=self.colors.q_values_norm,
            vmin=vmin,
            vmax=vmax,
            alpha=0.7
        )
        if self.write_values:
            for i in range(Q_values.shape[0]):
                for j in range(Q_values.shape[1]):
                    ax_Q.text(j, i, around(Q_values[i, j], 1),
                              ha='center', va='center')
        # action_ticks = around(linspace(self.actions[0], self.actions[-1], 11), decimals=2)
        # state_ticks = around(linspace(self.states[0], self.actions[-1], 11), decimals=2)
        # ax_Q.set_xticks(action_ticks)
        # ax_Q.set_yticks(state_ticks)

        ax_Q.set_xlabel('action space $A$')
        ax_Q.set_ylabel('state space $S$')
        frame_width_x = self.actions[-1] * .1
        ax_Q.set_xlim((self.actions[0] - frame_width_x,
                       self.actions[-1] + frame_width_x))

        frame_width_y = self.states[-1] * .05
        ax_Q.set_ylim((self.states[0] - frame_width_y,
                       self.states[-1] + frame_width_y))

        return image


class DiscreteQValueSubplotter(Subplotter):
    def __init__(self, agent, colors, write_values=False, vmin=None, vmax=None,
                 interp_n=100):
        super(DiscreteQValueSubplotter, self).__init__(colors)
        self.agent = agent
        self.states = squeeze(self.model.env.state_space[:])
        self.actions = squeeze(self.model.env.action_space[:])
        stateaction_grid = self.model.env.stateaction_space[:, :]
        self.states_grid = stateaction_grid[:, :, 0]
        self.actions_grid = stateaction_grid[:, :, 1]
        self.write_values = write_values
        self.vmin = vmin
        self.vmax = vmax

        self.int_actions = linspace(0, self.actions[-1], interp_n)
        self.int_states = linspace(0, self.states[-1], interp_n)
        self.int_actions_grid, self.int_states_grid = meshgrid(
            self.int_actions, self.int_states
        )
        self.int_sa = dstack(
            (self.int_actions_grid, self.int_states_grid)
        ).reshape((-1, 2))

    @property
    def model(self):
        return self.agent.Q_model

    def __get_min_max(self, Q_values):
        if (self.vmin is not None) and (self.vmax is not None):
            qmin = self.vmin
            qmax = self.vmax
        else:
            nonzero_Q = Q_values[Q_values.nonzero()]
            if len(nonzero_Q) == 0:
                return -1, 1
            else:
                qmin = nonzero_Q.min()
                qmax = nonzero_Q.max()
                return qmin, qmax
        return qmin, qmax

    def draw_on_axs(self, ax_Q, Q_values):
        f = RegularGridInterpolator(
            (self.actions, self.states),
            Q_values.T,
            method='linear'
        )
        int_Q_values = f(self.int_sa).reshape(self.int_states_grid.shape)

        vmin, vmax = self.__get_min_max(Q_values)
        image = ax_Q.pcolormesh(
            self.int_actions,
            self.int_states,
            int_Q_values,
            cmap=self.colors.cmap_q_values,
            vmin=vmin,
            vmax=vmax,
            alpha=0.5
        )
        if self.write_values:
            for i in range(Q_values.shape[0]):
                for j in range(Q_values.shape[1]):
                    ax_Q.text(j, i, around(Q_values[i, j], 1),
                              ha='center', va='center')
        action_ticks = around(self.actions, decimals=2)
        state_ticks = around(self.states, decimals=2)
        ax_Q.set_xticks(action_ticks)
        ax_Q.set_yticks(state_ticks)

        ax_Q.set_xlabel('action space $A$')
        ax_Q.set_ylabel('state space $S$')
        frame_width_x = self.actions[-1] * .1
        ax_Q.set_xlim((self.actions[0] - frame_width_x,
                       self.actions[-1] + frame_width_x))

        frame_width_y = self.states[-1] * .05
        ax_Q.set_ylim((self.states[0] - frame_width_y,
                       self.states[-1] + frame_width_y))

        return image

