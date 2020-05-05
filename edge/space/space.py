from itertools import product
import numpy as np


class Space:
    def __init__(self):
        pass

    def contains(self, x):
        raise NotImplementedError

    def __contains__(self, x):
        return self.contains(x)

    def sample(self):
        raise NotImplementedError


class DiscreteSpace(Space):
    def __init__(self):
        super(DiscreteSpace, self).__init__()

    def __getitem__(self, index):
        raise NotImplementedError

    def indexof(self, x):
        raise NotImplementedError

    def __iter__(self):
        return self.get_index_iterator()

    def get_index_iterator(self):
        raise NotImplementedError

    def sample_idx(self):
        raise NotImplementedError

    def sample(self):
        k = self.sample_idx()
        return self[k]


class DiscreteProductSpace(DiscreteSpace):
    def __init__(self, *sets):
        super(DiscreteProductSpace, self).__init__()
        self.sets = sets

    def contains(self, coordinates):
        if len(coordinates) != len(self.sets):
            raise ValueError(f"Size mismatch: expected {len(self.sets)}"
                             f" coordinates, received {len(coordinates)}")
        coordinates_and_sets = zip(coordinates, self.sets)

        def isin(args):
            x = args[0]
            s = args[1]
            return x in s
        return all(map(isin, coordinates_and_sets))

    def sample_idx(self):
        def sample_set(s):
            return s.sample_idx()
        return tuple(map(sample_set, self.sets))

    def __getitem__(self, index):
        if len(index) != len(self.sets):
            raise ValueError(f'Size mismatch: expected {len(self.sets)}'
                             f' coordinates, received {len(index)}')
        index_and_sets = list(zip(index, self.sets))

        def get_item(args):
            ind = args[0]
            s = args[1]
            return s[ind]
        return list(map(get_item, index_and_sets))

    def indexof(self, x):
        if len(x) != len(self.sets):
            raise ValueError(f'Size mismatch: expected {len(self.sets)}'
                             f' coordinates, received {len(coordinates)}')
        x_and_sets = zip(x, self.sets)

        def indexof_coord(args):
            x = args[0]
            s = args[1]
            return s.indexof(x)
        return tuple(map(indexof_coord, x_and_sets))

    def get_index_iterator(self):
        def get_idx_iter(s):
            return s.get_index_iterator()
        return product(*self.sets)


class DiscreteStateActionSpace(DiscreteProductSpace):
    def __init__(self, state_space, action_space):
        super(DiscreteStateActionSpace, self).__init__(
            state_space,
            action_space
        )
        self.state_space = state_space
        self.action_space = action_space


class DiscreteSubspace(DiscreteSpace):
    def __init__(self, space, idx_in_subspace):
        super(DiscreteSubspace, self).__init__()
        # TODO
