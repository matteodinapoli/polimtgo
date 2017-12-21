from reinforcement_learning.FQI_learner import *
from simulation.simulator import Simulator



class Simulator_RL(Simulator):
    rl_predictors_map = {}
    test_mode = True
    start = "2016-06-01 20:30:55"
    now_date = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
    sold_today = {}
    validation_reps = 10

    def get_datafile_name(self):
        return "Simulation_FQI"

    def build_investment_map(self):
        self.evaluate_available_sets()
        for set_dir in self.set_dirs:
            load_feature_selection_table(set_dir)
            prices_path = get_data_location() + "DATA\\MTGOprices\\Standard\\" + set_dir
            price_files = [f for f in listdir(prices_path) if isfile(join(prices_path, f))]
            for card_file in price_files:
                card_name = os.path.splitext(card_file)[0]
                """ consider only cards for which the feature selection table is defined"""
                if card_name in get_feature_selection_table(set_dir):
                    """ train the FQI learner and store it """
                    if card_name not in self.rl_predictors_map:
                        predictor = MTGO_Q_learner(set_dir, card_file, self.releases[set_dir], self.start, self.actual_episodes_n)
                        pprint("**** Learning " + str(card_name) + " model ****")
                        predictor.learn()
                        card_name = os.path.splitext(card_file)[0]
                        self.rl_predictors_map[card_name] = predictor
                    """ Q for possible buy action, having card = False """
                    Q_value, price = self.rl_predictors_map[card_name].get_Q_prediction(self.now_date, False)
                    self.data[card_name] = [price, Q_value[0]]

    def get_investment_margin_list(self):
        margin_list = []
        for card_name, info in self.data.copy().items():
            price = info[0]
            Q_buying = info[1][0]
            Q_no_action = info[1][1]
            if Q_buying > Q_no_action:
                margin_list.append([card_name, Q_buying, price])
        margin_list.sort(key=lambda x: x[1], reverse=True)
        self.datafile.write(str(margin_list) + "\n")
        return margin_list


    def fill_investment_portfolio(self, margin_list):
        get_total_market_price_MACD()
        for margin_tupla in margin_list:
            card_name = margin_tupla[0]
            today_buy_price = margin_tupla[2]
            """ buying using all budget on ordered Q_values one card after another """
            if card_name not in self.sold_today:
                quantity = int(self.budget / today_buy_price)
                if quantity > self.max_card_pieces:
                    quantity = self.max_card_pieces
                if quantity > 0:
                    self.buy_cards(card_name, quantity, today_buy_price)


    def manage_owned_cards(self, margin_list):
        self.sold_today.clear()
        for card_name, price_key in self.owned_cards.copy().items():

            Q_value, today_sell_price = self.rl_predictors_map[card_name].get_Q_prediction(self.now_date, True)
            Q_no_action = Q_value[0][0]
            Q_selling = Q_value[0][1]
            today_sell_price -= self.get_spread(today_sell_price)

            for past_price, quantity in price_key.copy().items():
                loss = past_price - today_sell_price
                loss_percentage = loss / float(past_price)
                if Q_selling > Q_no_action and (
                        loss_percentage > self.BH_stoploss_threshold or - loss_percentage > self.BH_stopgain_threshold):
                    self.sell_cards(card_name, past_price, today_sell_price)
                    self.sold_today[card_name] = True
                    if card_name in self.transactions:
                        self.transactions[card_name].append([quantity, -loss])
                    else:
                        self.transactions[card_name] = [[quantity, -loss]]


    def get_price_from_data_map(self, card_name):
        card_map = self.data[card_name]
        today_sell_price = card_map[0]
        today_sell_price -= self.get_spread(today_sell_price)
        return today_sell_price

    
    def validate_n_episodes(self):
        with open(get_data_location() + "SIM\\" + "_Episodes_Validation_Result.txt", "w") as validation_file:
            validation_file.write("**** " + str() + " ****\n")
            self.init_params_for_validation()
            for episodes in self.episodes_n:
                self.actual_episodes_n = episodes
                for i in range(self.validation_reps):
                    self.rl_predictors_map = {}
                    self.launch()
                pprint(self.results_episodes)
            for episodes, result_list in self.results_episodes.copy().items():
                budget = 0
                pos_n = 0
                pos = 0
                neg_n = 0
                neg = 0
                for tupla_res in result_list:
                    budget += tupla_res[0]
                    pos_n += tupla_res[1]
                    pos += tupla_res[2]
                    neg_n += tupla_res[3]
                    neg += tupla_res[4]
                budget = budget/float(len(result_list))
                pos_n = pos_n / float(len(result_list))
                pos = pos / float(len(result_list))
                neg_n = neg_n / float(len(result_list))
                neg = neg / float(len(result_list))
                validation_file.write("\n **** NUMERO DI EPISODI: " + str(episodes) + " ****\n")
                validation_file.write("BUDGET FINALE\n")
                validation_file.write(str(budget) + "\n")
                validation_file.write("Transazioni positive: " + str(pos_n) + "\n")
                validation_file.write("Guadagno totale: " + str(pos) + "\n")
                validation_file.write("Transazioni negative: " + str(neg_n) + "\n")
                validation_file.write("Perdita totale: " + str(neg) + "\n")





if __name__ == "__main__":
    sim = Simulator_RL()
    sim.validate_n_episodes()
    #sim.launch()













