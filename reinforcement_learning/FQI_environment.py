import re

import numpy as np
import pandas as pd
from mushroom.environments import Environment, MDPInfo
from mushroom.utils import spaces

from data_parsing.data_builder import *
from linear_regression.predictor_ARIMAX import get_feature_selection_table
from linear_regression.predictor_ARIMAX import load_feature_selection_table
from simulation.simulator import Simulator


class MTGOenv(Environment):

    def __init__(self, set_dir="TST", card_file="Botanical Sanctum.txt", train_start=1476050400000, train_end="2016-12-01 20:30:55"):
        self.__name__ = 'MTGOenv'

        self.data = None
        self.card_features = None
        self.set_dir = set_dir
        self.card_file = card_file
        self.start = train_start
        self.now_date = datetime.datetime.fromtimestamp(self.start/1000.0)
        self.end_date = datetime.datetime.strptime(train_end, "%Y-%m-%d %H:%M:%S")
        self.spread_getter = Simulator()
        self.total_price_MACD = None

        # Running time optimization maps
        self.seen_states = {}
        self.now_date_to_index_conversions = {}
        self.dates = []
        self.prices = []

        self.explore_all_dataset = True
        self.price_cache = 0
        self.state_cahce = []
        self.absorb_cache = False

        self._base_state = None

        # MDP parameters
        """ -1 == buy, 1 == sell"""
        self._discrete_actions = [-1., 1.]

        # MDP properties
        high = np.array([float("inf")])
        observation_space = spaces.Box(low=-high, high=high)
        action_space = spaces.Discrete(2)
        horizon = 100000
        gamma = .999
        mdp_info = MDPInfo(observation_space, action_space, gamma, horizon)

        super(MTGOenv, self).__init__(mdp_info)


    def reset(self, state=None):
        if state is None:
            price, features, abs = self.load_next_data(True, True)
            self._state = np.array(features)
            """ ownership of the card == 0 """
            self._state = np.append(self._state, 0)
        else:
            self._state = state

        return self._state


    def step(self, action):
        action = self._discrete_actions[action[0]]
        has_the_card = self._state[-1]
        self.now_date += datetime.timedelta(hours=24)
        price, features, absorbing = self.load_next_data(False, True, self.now_date)

        has_the_card_new = 0

        new_state = np.array(features)
        reward = price * action

        if reward > 0:
            """ selling """
            reward -= self.spread_getter.get_spread(price)
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

        self._base_state = self._state.copy()
        if self.explore_all_dataset:
            if action == self._discrete_actions[-1] and has_the_card == 0:
                """ set has the card """
                self._state[-1] = 1
            if action == self._discrete_actions[-1] and has_the_card == 1:
                self._state = new_state
                self._state[-1] = 0
            else:
                """ exploring the other actions of the day """
                self.now_date -= datetime.timedelta(hours=24)
        else:
            self._state = new_state

        return new_state.copy(), reward, absorbing, {}



    def load_next_data(self, reset, store_state, now_date=None):

        if reset:
            self.now_date = datetime.datetime.fromtimestamp(self.start/1000.0)
            now_date = self.now_date
        normalized = False
        if not self.data:
            time_series = get_base_timeseries(self.set_dir, self.card_file, datetime.datetime.now(), normalized)
            self.data = time_series
        else:
            time_series = self.data

        card_name = os.path.splitext(self.card_file)[0]

        if not self.card_features:
            feature_selection_table = get_feature_selection_table(self.set_dir)
            if not feature_selection_table:
                load_feature_selection_table(self.set_dir)
                feature_selection_table = get_feature_selection_table(self.set_dir)
            formula = feature_selection_table[card_name]
            features = re.compile('[A-Za-z]+').findall(formula)
            features.sort()
            self.card_features = features

        if not self.dates or self.prices:
            timePriceList = time_series[0]
            self.dates = [x[0] for x in timePriceList]
            self.prices = [x[1] for x in timePriceList]
        dates = self.dates
        prices = self.prices

        if self.now_date < dates[0]:
            self.now_date = dates[0]
            self.now_date = self.now_date.replace(hour=22, minute=0)
            if not now_date:
                now_date = self.now_date

        if not now_date in self.now_date_to_index_conversions:
            actual_date = min(dates, key=lambda x: abs(x - now_date) if (x - now_date) < datetime.timedelta(0) else 1000 * abs(x - now_date))
            self.now_date_to_index_conversions[now_date] = actual_date
        else:
            actual_date = self.now_date_to_index_conversions[now_date]

        if store_state and actual_date in self.seen_states:
            return self.seen_states[actual_date]
        else:
            data = {"dates": dates, "prices": prices}
            for feat in self.card_features:
                feat_index = get_feature_to_index_map()[feat]
                double_list = time_series[feat_index]
                data_list = [x[1] for x in double_list]
                data[feat] = data_list

            columns_df = self.card_features.copy().extend(('dates', 'prices', 'totalMACD'))
            df = pd.DataFrame(data, columns= columns_df)
            df.index = df['dates']

            price_pair = df.loc[:actual_date, "prices"].tail(2)
            if len(price_pair) > 1:
                price = price_pair[1]
                prev_price = price_pair[0]
            else:
                price = price_pair[0]
                prev_price = price

            state = []
            for feat in self.card_features:
                if feat == 'prices':
                    """ AR1 feature """
                    # SUBSTITUTED WITH PRICE OF CURRENT DAY
                    #state.append(prev_price)
                    state.append(price)
                else:
                    """ exogenous features """
                    state.append(df.loc[actual_date, feat])

            if not self.total_price_MACD:
                self.total_price_MACD = get_total_market_price_MACD_dict()
            key_string = actual_date.strftime('%y%m%d')
            total_market_indicator = self.total_price_MACD[key_string]
            state.append(total_market_indicator)

            time_diff = self.end_date - actual_date
            """ state is absorbing and final if difference of actual date and end of training is lesser than one day """
            absorb = time_diff/datetime.timedelta(days=1) < 1 or actual_date > self.end_date

            if store_state:
                self.seen_states[actual_date] = price, state, absorb

        return price, state, absorb


if __name__ == "__main__":
    mdp = MTGOenv()