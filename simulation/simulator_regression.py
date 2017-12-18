# coding=utf-8

from data_parsing.data_builder import *

from linear_regression.predictor_ARIMAX import get_ARIMAX_prediction
from linear_regression.predictor_ARIMAX import save_feature_selection_table
from simulation.simulator import Simulator



class Simulator_Regression(Simulator):

    """ start date of simulation """
    start = "2017-01-01 20:30:55"
    now_date = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
    test_mode = True
    use_confidence_interval = True



    def get_datafile_name(self):
        return "Simulation_Regression"


    def get_investment_margin_list(self):
        margin_list = []

        for card_name, dicts_list in self.data.copy().items():
            current_key = self.find_current_time_key(dicts_list[0], self.now_date)
            next_key = self.find_next_time_key(dicts_list[1], self.now_date)
            if current_key in dicts_list[0]:
                today_buy_price = dicts_list[0][current_key]
                if next_key in dicts_list[1]:
                    tomorrow_sell_price = dicts_list[1][next_key]
                    tomorrow_sell_price_conf_10 = dicts_list[2][next_key]
                    if self.use_confidence_interval:
                        margin = tomorrow_sell_price_conf_10 - today_buy_price
                    else:
                        margin = tomorrow_sell_price - today_buy_price
                    margin_list.append([card_name, margin, today_buy_price, tomorrow_sell_price, tomorrow_sell_price_conf_10])
                else:
                    pprint("PREDICTION DI DOMANI " + str(next_key) + " NON PRESENTE PER " + str(card_name))
            else:
                pprint("PREZZO DI OGGI " + str(current_key) + " NON PRESENTE PER " + str(card_name))

        margin_list.sort(key=lambda x: x[1]/x[2], reverse=True)

        return margin_list


    def build_investment_map(self):
        self.evaluate_available_sets()
        for set_dir in self.set_dirs:

            prices_path = get_data_location() + "DATA\\MTGOprices\\Standard\\" + set_dir
            price_files = [f for f in listdir(prices_path) if isfile(join(prices_path, f))]
            for card_file in price_files:
                df_list = get_ARIMAX_prediction(set_dir, card_file, self.datafile, False, False, self.now_date, True)
                if df_list is not None:
                    df = df_list[0]
                    predicted_df = df_list[1]
                    prices_raw = df.ix[-2:]['prices'].to_dict()
                    prices = {key.to_datetime().replace(minute=0, second=0, microsecond=0): val for key, val in prices_raw.copy().items()}
                    predicted_prices_raw = predicted_df['prices'].to_dict()
                    predicted_prices = {key.to_datetime().replace(minute=0, second=0, microsecond=0) : val for key, val in predicted_prices_raw.copy().items()}
                    """confidence intervals 10"""
                    confidence_delta_10 = df_list[2][1]
                    predicted_prices_10 = {key: val - confidence_delta_10 for key, val in predicted_prices.copy().items()}
                    card_name = os.path.splitext(card_file)[0]
                    self.data[card_name] = [prices, predicted_prices, predicted_prices_10]
                else:
                    if os.path.splitext(card_file)[0] in self.data:
                        pprint("ATTENZIONE: PREDICTION DI " + str(card_file) + " NON HA ELABORATO UN RISULTATO\n")
                        del self.data[os.path.splitext(card_file)[0]]
            save_feature_selection_table(set_dir)


    def fill_investment_portfolio(self, margin_list):
        for margin_tupla in margin_list:

            card_name = margin_tupla[0]
            margin = margin_tupla[1]
            today_buy_price = margin_tupla[2]
            if self.use_confidence_interval:
                tomorrow_sell_price = margin_tupla[4]
            else:
                tomorrow_sell_price = margin_tupla[3]

            if margin > self.buy_threshold + self.get_spread(tomorrow_sell_price):
                """ acquistiamo """
                quantity = int(self.budget/today_buy_price)
                if quantity > self.max_card_pieces:
                    quantity = self.max_card_pieces
                if quantity > 0:
                    self.buy_cards(card_name, quantity, today_buy_price)


    def manage_owned_cards(self, margin_list):
        for card_name, price_key in self.owned_cards.copy().items():
            card_map = self.data[card_name]

            """ selling we always use the not confidence interval reduced tomorrow sell price prediction 
            to change it, put to 2 next_price_index in the if part """
            if self.use_confidence_interval:
                next_price_index = 1
            else:
                next_price_index = 1

            current_key = self.find_current_time_key(card_map[0], self.now_date)
            next_key = self.find_next_time_key(card_map[next_price_index], self.now_date)

            today_sell_price = card_map[0][current_key]
            today_sell_price -= self.get_spread(today_sell_price)

            tomorrow_sell_price = card_map[next_price_index][next_key]
            tomorrow_sell_price -= self.get_spread(tomorrow_sell_price)

            for past_price, quantity in price_key.copy().items():
                loss = past_price - today_sell_price
                loss_percentage = loss/float(past_price)
                if today_sell_price >= tomorrow_sell_price and (loss_percentage > self.BH_stoploss_threshold or - loss_percentage > self.BH_stopgain_threshold):
                    self.sell_cards(card_name, past_price, today_sell_price)
                    if card_name in self.transactions:
                        self.transactions[card_name].append([quantity, -loss])
                    else:
                        self.transactions[card_name] = [[quantity, -loss]]

    def get_price_from_data_map(self, card_name):
        card_map = self.data[card_name]
        current_key = self.find_current_time_key(card_map[0], self.now_date)
        today_sell_price = card_map[0][current_key]
        today_sell_price -= self.get_spread(today_sell_price)
        return today_sell_price



if __name__ == "__main__":
    sim = Simulator_Regression()
    sim.launch()
