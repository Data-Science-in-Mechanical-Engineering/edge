import numpy as np
from scipy.stats import norm
from pathlib import Path
import warnings, contextlib
import json

from .. import GPModel
from ..inference import MaternGP


class SafetyMeasure(GPModel):
    """
    Safety measure as described in "A learnable safety measure", by Heim, von Rohr, et al. (2019, CoRL).
    """

    def __init__(self, env, gp, gamma_measure):
        """
        Initializer
        :param env: the environment
        :param gp: the underlying GP
        :param gamma_measure: the gamma coefficient used by the measure. It corresponds to gamma_optimistic

        Note: the measure has no information about the gamma_cautious parameter: it is a parameter of the policy,
        not the measure. Hence, we rename gamma_optimistic to gamma_measure, since it is the only gamma parameter of the
        measure.
        """
        super(SafetyMeasure, self).__init__(env, gp)
        self.gamma_measure = gamma_measure

    @property
    def state_dict(self):
        return {
            'gamma_measure': self.gamma_measure
        }

    def update(self, state, action, new_state, reward, failed, done, measure=None):
        """
        Updates the underlying GP with the measure computation update
        :param state: the previous state
        :param action: the action taken
        :param new_state: the new state
        :param reward: the reward incurred
        :param failed: whether the agent has failed
        """
        if not failed and measure is None:
            update_value = self.measure(
                state=new_state,
                lambda_threshold=0,
                gamma_threshold=self.gamma_measure
            )
        elif not failed and measure is not None:
            update_value = np.atleast_1d(measure)
        else:
            update_value = np.array([0.])

        stateaction = self.env.stateaction_space[state, action]
        self.gp.append_data(stateaction, update_value, forgettable=[not failed],
                            make_forget=[not failed],
                            unskippable=[failed])
        return update_value

    def measure(self, state, lambda_threshold=0, gamma_threshold=None):
        """
        Computes the safety measure in the state passed as parameter with the given thresholds.
        :param state: np.ndarray: the state or list of states where to compute the measure
        :param lambda_threshold: (default=0) the lambda parameter
        :param gamma_threshold: (default=gamma_measure) the gamma parameter
        :return: the measure at the given state(s)
        """
        if gamma_threshold is None:
            gamma_threshold = self.gamma_measure

        level_set = self.level_set(state, lambda_threshold, gamma_threshold,
                                   return_proba=False, return_covar=False)

        level_set = level_set.reshape((-1,) + self.env.action_space.shape)
        mean_axes = tuple([1 + k
                           for k in range(self.env.action_space.index_dim)])

        return np.atleast_1d(level_set.mean(mean_axes))

    def is_in_level_set(self, state, action, lambda_threshold, gamma_threshold):
        measure, covar = self.query((state, action), return_covar=True)
        level_value = norm.cdf((measure - lambda_threshold) / np.sqrt(covar))
        return np.squeeze(level_value > gamma_threshold)

    def level_set(self, state, lambda_threshold, gamma_threshold,
                  return_proba=False, return_covar=False, return_measure=False,
                  return_covar_matrix=False):
        """
        Computes the probabilistic level set of the GP on the stateaction space. The output is a boolean array which
        is True whenever the stateaction is within the level set.
        If you want to consider multiple lambda and gamma thresholds, calling this method with a list of thresholds
        is more efficient than calling it multiple times. Note that when calling it with lists, the two lists should
        have the same length.
        :param state: the state or list of state from where we compute the level set
        :param lambda_threshold: the value or list of values to consider for the lambda threshold
        :param gamma_threshold: the value or list of values to consider for the gamma threshold
        :param return_proba: whether to return the probabilities associated to each state-action having a measure
        higher than the threshold
        :param return_covar: whether to return the covariance at each state-action
        :param return_measure: whether to return the actual values of the measure instead of the level set only
        :return: depending on the values of return_[proba,covar,measure], either a single array or a tuple of arrays
        is returned. Moreover, if lambda_threshold and gamma_threshold are lists, each array is replaced by a list of
        the arrays corresponding to each value for the thresholds.
        The first three arrays have the same shape : (state.shape[0],) + action_space.shape
        The last one has shape (state.shape[0],)
            * np.ndarray<boolean>: level set
            * np.ndarray<float>: probability of each state-action being above the lambda threshold
            * np.ndarray<float>: covariance at each state-action
            * np.ndarray<float>: value of the measure at each state
        """
        # We allow calling this function on different lambdas and gammas
        # to avoid multiple inference passes
        if not isinstance(lambda_threshold, (list, tuple)):
            lambda_threshold_list = [lambda_threshold]
        else:
            lambda_threshold_list = lambda_threshold
        if not isinstance(gamma_threshold, (list, tuple)):
            gamma_threshold_list = [gamma_threshold]
        else:
            gamma_threshold_list = gamma_threshold

        if state is None:
            # Unspecfied state means the whole state space
            index = (slice(None, None, None), slice(None, None, None))
        elif isinstance(state, slice):
            index = (state, slice(None, None, None))
        elif state.ndim > 1 and state.shape[0] > 1:
            # This means `state` is a list of states
            index = [
                (*s.reshape(-1, 1), slice(None, None, None)) for s in state
            ]
        else:
            index = (*state.reshape(-1, 1), slice(None, None, None))
        output_shape = (-1,) + self.env.action_space.shape

        query_out = self.query(
            index,
            return_covar=True,
            return_covar_matrix=return_covar_matrix,
        )
        if return_covar_matrix:
            measure_slice, covar_slice, covar_matrix = query_out
        else:
            measure_slice, covar_slice = query_out
            covar_matrix = None
        measure_slice = measure_slice.reshape(output_shape)
        covar_slice = covar_slice.reshape(output_shape)
        if covar_matrix is not None:
            # The covar_matrix does not have the same shape as the other two:
            # its number of lines is n_states x n_actions, whereas the number of
            # lines of the others is simply n_states.
            covar_matrix = covar_matrix.reshape(output_shape)

        # The following prints a user-friendly warning if a runtime warning is encountered in the computation of
        # level_value_list
        # If the kernel matrix is ill-conditioned, the covariance may be negative
        # This will raise a RuntimeWarning in np.sqrt(covar_slice)
        # See https://github.com/cornellius-gp/gpytorch/issues/1037
        with warnings.catch_warnings(record=True) as w:
            # The contextmanager decorator enables the use of the function in a `with` statement, and
            # requires that the function is a generator
            # This function simply returns the list it computes
            @contextlib.contextmanager
            def compute_cdf():
                try:
                    yield [
                        norm.cdf(
                            (measure_slice - lambda_threshold) / np.sqrt(covar_slice)
                        ) for lambda_threshold in lambda_threshold_list
                    ]
                finally:
                    pass

            with compute_cdf() as cdf_list:  # The list computed by compute_cdf is stored in cdf_list
                if len(w) > 0:  # We check whether a warning was raised to change its message
                    original_warning = ''
                    for wrng in w:
                        original_warning += str(wrng.message) + '\n'
                    original_warning = original_warning[:-2]
                    warning_message = (
                                'Warning encountered in cumulative density function computation. \nThis may be '
                                'caused by an ill-conditioned kernel matrix causing a negative covariance.\n'
                                'Original warning: ' + str(original_warning))
                    level_value_list = [
                        norm.cdf(
                            (measure_slice - lambda_threshold) / np.sqrt(np.abs(covar_slice))
                        ) for lambda_threshold in lambda_threshold_list
                    ]
                else:
                    warning_message = None
                    level_value_list = cdf_list  # We store cdf_list so its value is available outside of `with`
        if warning_message is not None:
            warnings.warn(warning_message)

        level_set_list = [level_value > gamma_threshold
                          for level_value, gamma_threshold in
                          zip(level_value_list, gamma_threshold_list)]

        if len(level_set_list) == 1:
            level_set_list = level_set_list[0]
            level_value_list = level_value_list[0]

        return_var = (level_set_list,) if any((return_proba,
                                               return_covar,
                                               return_measure,
                                               return_covar_matrix)) \
            else level_set_list
        if return_proba:
            return_var += (level_value_list,)
        if return_covar:
            return_var += (covar_slice,)
        if return_measure:
            return_var += (measure_slice,)
        if return_covar_matrix:
            return_var += (covar_matrix,)

        return return_var


class MaternSafety(SafetyMeasure):
    def __init__(self, env, gamma_measure, x_seed, y_seed, gp_params=None):
        """
        Initializer
        :param env: the environment
        :param gamma_measure: the gamma coefficient used by the measure. It corresponds to gamma_optimistic
        :param x_seed: the seed input of the GP: a list of stateactions
        :param y_seed: the seed output of the GP: a list of floats
        :param gp_params: the parameters defining the GP. See edge.models.inference.MaternGP for more information
        """
        if gp_params is None:
            gp_params = {}
        gp = MaternGP(x_seed, y_seed, **gp_params)
        super(MaternSafety, self).__init__(env, gp, gamma_measure)

    @staticmethod
    def load(load_folder, env, gamma_measure, x_seed, y_seed):
        """
        Loads the model and the GP saved by the GPModel.save method. Note that this method may fail if the save was
        made with an older version of the code.
        :param load_folder: the folder where the files are
        :return: MaternSafety: the model
        """
        load_path = Path(load_folder)
        gp_load_path = str(load_path / GPModel.GP_SAVE_NAME)

        load_data = x_seed is None
        gp = MaternGP.load(gp_load_path, x_seed, y_seed, load_data=load_data)
        if load_data:
            x_seed = gp.train_x
            y_seed = gp.train_y

        if gamma_measure is None:
            model_save_path = str(load_path / GPModel.SAVE_NAME)
            try:
                with open(model_save_path, 'r') as f:
                    json_str = f.read()
                    state_dict = json.loads(json_str)
                gamma_measure = state_dict['gamma_measure']
            except FileNotFoundError:
                raise ValueError(f'Could not find file {model_save_path}. '
                                 f'Specify gamma_measure instead to load this '
                                 f'model')

        model = MaternSafety(env, gamma_measure=gamma_measure,
                             x_seed=x_seed, y_seed=y_seed)
        model.gp = gp

        return model
