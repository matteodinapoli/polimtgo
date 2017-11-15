import numpy as np
from scipy.integrate import odeint

from mushroom.environments import Environment, MDPInfo
from mushroom.utils import spaces
from data_builder import *
from simulator import get_spread
import pandas as pd


class MTGOenv(Environment):



    def __init__(self, set_dir="TST", card_file="Botanical Sanctum.txt"):
        self.__name__ = 'MTGOenv'

        self.data = None
        self.set_dir = set_dir
        self.card_file = card_file
        self.start = "2017-01-01 20:30:55"
        self.now_date = datetime.datetime.strptime(self.start, "%Y-%m-%d %H:%M:%S")

        # MDP parameters
        """ -1 == sell, 1 == buy"""
        self._discrete_actions = [-1., 1.]

        # MDP properties
        high = np.array([float("inf")])
        observation_space = spaces.Box(low=-high, high=high)
        action_space = spaces.Discrete(2)
        horizon = 100
        gamma = .95
        mdp_info = MDPInfo(observation_space, action_space, gamma, horizon)

        super(MTGOenv, self).__init__(mdp_info)


    def reset(self, state=None):
        if state is None:
            price, features, abs = self.load_next_data(True)
            self._state = np.array(features)
            """ ownership of the card == 0 """
            self._state = np.append(self._state, 0)
        else:
            self._state = state

        return self._state


    def step(self, action):
        action = self._discrete_actions[action[0]]

        price, features, absorbing = self.load_next_data(False)
        has_the_card = self._state[-1]
        has_the_card_new = 0

        new_state = np.array(features)
        reward = price * action

        if reward > 0:
            """ selling """
            reward -= get_spread(price)
            """ reward = 0 if doesn't own the card to sell """
            reward = reward * has_the_card
        else:
            """ buying """
            has_the_card_new = 1
            if has_the_card == has_the_card_new:
                reward = 0
            else:
                reward = - price

        new_state = np.append(new_state, has_the_card_new)
        self._state = new_state

        return self._state, reward, absorbing, {}


    def load_next_data(self, reset):

        if reset:
            self.now_date = datetime.datetime.strptime(self.start, "%Y-%m-%d %H:%M:%S")

        normalized = False
        if not self.data:
            time_series = get_base_timeseries(self.set_dir, self.card_file, datetime.datetime.now(), normalized)
            self.data = time_series
        else:
            time_series = self.data

        timePriceList = time_series[0]
        standardizedTourCount = time_series[1]
        MACD_index = time_series[8]

        dates = [x[0] for x in timePriceList]
        prices = [x[1] for x in timePriceList]
        tours = [x[1] for x in standardizedTourCount]
        MACD = [x[1] for x in MACD_index]

        actual_date = min(dates, key=lambda x: abs(x - self.now_date) if (x - self.now_date) > datetime.timedelta(0) else 1000*abs(x - self.now_date))

        data = {"dates": dates, "prices": prices, "usage": tours, "MACD": MACD}
        df = pd.DataFrame(data, columns=['dates', 'prices', 'usage', 'MACD'])
        df.index = df['dates']
        del df['dates']

        price = df.loc[actual_date, "prices"]
        usage = df.loc[actual_date, "usage"]
        MACD = df.loc[actual_date, "MACD"]

        absorb = actual_date == dates[-1]

        self.now_date += datetime.timedelta(hours=24)

        return price, [usage, MACD], absorb


if __name__ == "__main__":
    mdp = MTGOenv()