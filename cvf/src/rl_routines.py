""" RL-Routines
"""
import torch
import rlog


class Episode:
    """ An iterator accepting an environment and a policy, that returns
    experience tuples.
    """

    def __init__(self, env, policy, _state=None):
        self.env = env
        self.policy = policy
        self.__R = 0
        self.__step_cnt = -1
        if _state is None:
            self.__state, self.__done = self.env.reset(), False
        else:
            self.__state, self.__done = _state, False

    def __iter__(self):
        return self

    def __next__(self):
        if self.__done:
            raise StopIteration

        _pi = self.policy.act(self.__state)
        _state = self.__state.clone()
        self.__state, reward, self.__done, _ = self.env.step(_pi.action)

        self.__R += reward
        self.__step_cnt += 1
        return (_state, _pi, reward, self.__state, self.__done)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        print("Episode done")

    @property
    def Rt(self):
        """ Return the expected return.
        """
        return self.__R

    @property
    def steps(self):
        """ Return steps taken in the environment.
        """
        return self.__step_cnt


def validate(policy, env, steps):
    """ Validation routine """
    done_eval, step_cnt = False, 0
    with torch.no_grad():
        while not done_eval:
            for _, _, reward, _, done in Episode(env, policy):
                rlog.put(reward=reward, done=done, val_frames=1)
                step_cnt += 1
                if step_cnt >= steps:
                    done_eval = True
                    break
    env.close()


def train_rounds(steps, interval):
    """ Returns a generator of tuples making a training round.

    Args:
        steps (int): Total number of training steps.
        interval (int): Frequency of training rounds.

    Returns:
        generator: Generator of (start, end) tuples.

    Example:
        steps, interval = 1_000_000, 5_000
        val_freq = 5_000

        [(0, 5000), (5000, 10000), ...]
    """
    return (
        (i * interval, (i * interval) + interval)
        for i in range(steps // interval)
    )
