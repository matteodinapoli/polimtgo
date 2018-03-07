from joblib import Parallel, delayed
from mushroom.algorithms.value.batch_td import FQI
from mushroom.core.core import Core
from mushroom.policy import EpsGreedy
from mushroom.utils.parameters import Parameter
from sklearn.ensemble import ExtraTreesRegressor

from reinforcement_learning.FQI_environment import *


class MTGO_Q_learner:
    agent = None

    def __init__(self, set_dir="TST", card_file="Botanical Sanctum.txt", train_start="2016-01-01 20:30:55", train_end="2016-12-01 20:30:55", episodes = 1000, min_split = 5):
        self.mdp = MTGOenv(set_dir, card_file, train_start, train_end)
        self.episodes_n = episodes
        self.split_n = min_split


    def learn(self):

        np.random.seed()
        # Policy
        epsilon = Parameter(value=1.)
        pi = EpsGreedy(epsilon=epsilon)
        # Approximator
        approximator_params = dict(input_shape=self.mdp.info.observation_space.shape,
                                   n_actions=self.mdp.info.action_space.n,
                                   n_estimators=50,
                                   min_samples_split= self.split_n,
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
        how_many = self.episodes_n
        if hasattr(self.mdp, 'explore_all_dataset'):
            if self.mdp.explore_all_dataset:
                how_many = 1
        core.learn(n_iterations=1, how_many=how_many, n_fit_steps=20, iterate_over='episodes')


    def get_Q_prediction(self, now_date, has_the_card):

        price, state, absorbing = self.mdp.load_next_data(False, False, now_date)
        if has_the_card:
            state.append(1)
        else:
            state.append(0)
        np_state = np.array([state])
        return self.agent.approximator.predict(np_state), price


    def get_Q_error(self, now_date, end_date, has_the_card):
        reward = 0
        Q_to_evaluate = None
        while now_date < end_date:
            Q_value, price = self.get_Q_prediction(now_date, has_the_card)
            Q_buy_or_no_action = Q_value[0][0]
            Q_sell_or_no_action = Q_value[0][1]
            if not Q_to_evaluate:
                Q_to_evaluate = max(Q_buy_or_no_action, Q_sell_or_no_action)
            if not has_the_card:
                if Q_buy_or_no_action > Q_sell_or_no_action:
                    has_the_card = True
                    reward -= price
            else:
                if Q_sell_or_no_action > Q_buy_or_no_action:
                    has_the_card = False
                    reward += (price - self.mdp.spread_getter.get_spread(price))
            now_date += datetime.timedelta(hours=24)

        """ sell the card at the end if still possess it """
        if has_the_card:
            has_the_card = False
            Q_value, price = self.get_Q_prediction(now_date, has_the_card)
            reward += (price - self.mdp.spread_getter.get_spread(price))

        return abs(Q_to_evaluate - reward)




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
