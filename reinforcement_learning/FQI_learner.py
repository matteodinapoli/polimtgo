from joblib import Parallel, delayed
from mushroom.algorithms.value.batch_td import FQI
from mushroom.core.core import Core
from mushroom.policy import EpsGreedy
from mushroom.utils.parameters import Parameter
from sklearn.ensemble import ExtraTreesRegressor

from reinforcement_learning.FQI_environment import *


class MTGO_Q_learner:
    agent = None

    def __init__(self, set_dir="TST", card_file="Botanical Sanctum.txt", train_start="1476050400000", train_end="2016-12-01 20:30:55"):
        self.mdp = MTGOenv(set_dir, card_file, train_start, train_end)


    def learn(self):

        np.random.seed()
        # Policy
        epsilon = Parameter(value=1.)
        pi = EpsGreedy(epsilon=epsilon)
        # Approximator
        approximator_params = dict(input_shape=self.mdp.info.observation_space.shape,
                                   n_actions=self.mdp.info.action_space.n,
                                   n_estimators=50,
                                   min_samples_split=5,
                                   min_samples_leaf=2)
        approximator = ExtraTreesRegressor

        # Agent
        algorithm_params = dict()
        fit_params = dict()
        agent_params = {'approximator_params': approximator_params,
                        'algorithm_params': algorithm_params,
                        'fit_params': fit_params}

        self.agent = FQI(approximator, pi, self.mdp.info, agent_params) # quinto parametro le features

        # Algorithm
        core = Core(self.agent, self.mdp)
        # Train
        core.learn(n_iterations=1, how_many=1000, n_fit_steps=20, iterate_over='episodes')


    def get_Q_prediction(self, now_date, has_the_card):

        price, state, absorbing = self.mdp.load_next_data(False, False, now_date)
        if has_the_card:
            state.append(1)
        else:
            state.append(0)
        np_state = np.array([state])
        return self.agent.approximator.predict(np_state), price



if __name__ == '__main__':
    """#Js = Parallel(n_jobs=-1)(delayed(learner.learn)() for _ in range(n_experiment))
    #print(np.mean(Js))



    core.reset()

    # Test
    test_epsilon = Parameter(0.)
    agent.policy.set_epsilon(test_epsilon)

    initial_states = np.zeros((289, 2))
    cont = 0
    for i in range(-8, 9):
        for j in range(-8, 9):
            initial_states[cont, :] = [0.125 * i, 0.375 * j]
            cont += 1

    dataset = core.evaluate(initial_states=initial_states)

    return np.mean(compute_J(dataset, mdp.info.gamma))
    """
