from reinforcement_learning.FQI_learner import *
from simulation.simulator import Simulator
import re
import scipy.stats as st




class Simulator_RL(Simulator):

    test_mode = False
    start = "2016-08-01 20:30:55"
    now_date = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
    rl_predictors_map = {}
    sold_today = {}
    Q_threshold = 0.1
    simulation_steps = 60
    split_n = [100, 80, 60, 50, 40, 30, 20, 15, 10, 5, 2]
    actual_split_n = 2

    validation_reps = 10


    def get_datafile_name(self):
        return "Simulation_FQI"

    def build_investment_map(self):
        #if not self.set_dirs:
        self.evaluate_available_sets()
        self.data.clear()
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
                        #predictor = MTGO_Q_learner(set_dir, card_file, self.releases[set_dir], self.start, self.actual_episodes_n, self.actual_split_n)
                        predictor = MTGO_Q_learner(set_dir, card_file, self.releases[set_dir], self.now_date.strftime("%Y-%m-%d %H:%M:%S"),
                                                   self.actual_episodes_n, self.actual_split_n)
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
            threshold = Q_buying * self.Q_threshold
            delta = Q_buying - Q_no_action
            if Q_buying > 0 and delta > threshold:
                margin_list.append([card_name, Q_buying, Q_no_action, price])
        """ sorted by difference of the two Q values """
        margin_list.sort(key=lambda x: x[1] - x[2], reverse=True)
        self.datafile.write(str(margin_list) + "\n")
        return margin_list


    def fill_investment_portfolio(self, margin_list):
        for margin_tupla in margin_list:
            card_name = margin_tupla[0]
            today_buy_price = margin_tupla[3]
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

    
    def validate_Q_on_episodes_number(self, n):
        self.validate_Q_value_on_parameters_error_difference(self.episodes_n, "Episodes", n)

    def validate_Q_on_min_sample_split(self, n):
        self.validate_Q_value_on_parameters_error_difference(self.split_n, "Split", n)

    def validate_Q_value_on_parameters_error_difference(self, parameter_list, changing_parameter, n=0):
        with open(get_data_location() + "SIM\\" + "Q_validation_result_" + str(changing_parameter) + "_" + str((datetime.datetime.strptime(self.start, "%Y-%m-%d %H:%M:%S")).strftime("%Y_%m")) + "_" + str(n) + ".txt", "w") as validation_file:
            validation_file.write("\n **** Validation Start Date: " + str(self.now_date) + " ****\n")
            end_date = self.now_date + (datetime.timedelta(hours=24) * self.simulation_steps)
            Q_value_parameters_map = {}
            for parameter in parameter_list:
                if changing_parameter == "Episodes":
                    self.actual_episodes_n = parameter
                if changing_parameter == "Split":
                    self.actual_split_n = parameter
                self.now_date = datetime.datetime.strptime(self.start, "%Y-%m-%d %H:%M:%S")
                self.rl_predictors_map.clear()
                self.data.clear()
                self.build_investment_map()

                Q_value_card_map = {}
                for card_name, info in self.data.copy().items():
                    Q_value_list = []
                    self.now_date = datetime.datetime.strptime(self.start, "%Y-%m-%d %H:%M:%S")
                    while self.now_date < end_date:
                        Q_value_t, price = self.rl_predictors_map[card_name].get_Q_prediction(self.now_date, True)
                        Q_value_f, price = self.rl_predictors_map[card_name].get_Q_prediction(self.now_date, False)
                        Q_value = np.concatenate([Q_value_t[0], Q_value_f[0]])
                        Q_value_list.append(Q_value)
                        self.now_date += datetime.timedelta(hours=24)
                    Q_value_card_map[card_name] = Q_value_list
                Q_value_parameters_map[parameter] = Q_value_card_map

            pivot_card_map = Q_value_parameters_map[parameter_list[-1]]
            pivot_items = pivot_card_map.copy().items()
            for parameter in parameter_list[:-1]:

                pprint("**** Valore Parametro " + str(changing_parameter) + ": " + str(parameter) + " ****")
                validation_file.write("\n **** Valore Parametro " + str(changing_parameter) + ": " + str(parameter) + " ****\n")

                comparison_map = Q_value_parameters_map[parameter]
                base = None
                for card_name, Q_list in pivot_items:
                    comparison_list = comparison_map[card_name]
                    if base is None:
                        base = np.square(np.subtract(Q_list, comparison_list))
                    else:
                        base = np.vstack([base, np.square(np.subtract(Q_list, comparison_list))])
                MSE = np.average(base)
                validation_file.write(" - MSE: " + str(MSE) + "\n")
                SSE = np.sum(base)
                validation_file.write(" - SSE: " + str(SSE) + "\n")
                variance = np.var(base)
                validation_file.write(" - Variance: " + str(variance) + "\n")


    def analyze_Q_validation_files(self):
        files_path = get_data_location() + "Q_validation"
        validation_files = [f for f in listdir(files_path) if isfile(join(files_path, f))]
        validation_lists = []
        title_list = []
        for validation_file_name in validation_files:
            f = open(join(files_path, validation_file_name), "r")
            title_list.append(validation_file_name)
            key_list = []
            sse_list = []
            for line in f:
                if "Valore Parametro" in line:
                    key_list.append(float(re.findall(r"[-+]?\d*\.\d+|\d+", line)[0]))
                elif "SSE" in line:
                    sse_list.append(float(re.findall(r"[-+]?\d*\.\d+|\d+", line)[0]))
            f.close()
            sse_list = normalize_list(sse_list)
            tuple_list = list(zip(key_list, sse_list))
            #del tuple_list[0]
            validation_lists.append(tuple_list)
        make_Q_validation_graph(validation_lists, title_list, "Min Split Validation SSE")


    """
        def validate_n_episodes_on_model_performance(self):
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


    def validate_Q_value_on_effective_reward(self):
        with open(get_data_location() + "SIM\\" + "Q_validation_result.txt", "w") as validation_file:
            validation_file.write("\n **** Validation Start Date: " + str(self.now_date) + " ****\n")
            for episodes in self.episodes_n:
                self.actual_episodes_n = episodes
                pprint("**** NUMERO DI EPISODI: " + str(episodes) + " ****")
                validation_file.write("\n **** NUMERO DI EPISODI: " + str(episodes) + " ****\n")

                self.process_validation(validation_file)


    def process_validation(self, validation_file):
        total_error = 0
        self.now_date = datetime.datetime.strptime(self.start, "%Y-%m-%d %H:%M:%S")
        self.rl_predictors_map.clear()
        self.data.clear()
        self.build_investment_map()
        end_date = self.now_date + (datetime.timedelta(hours=24) * self.simulation_steps)

        for card_name, info in self.data.copy().items():
            pprint(card_name)
            total_error += (self.rl_predictors_map[card_name].get_Q_error(self.now_date, end_date, True)) ** 2
            total_error += (self.rl_predictors_map[card_name].get_Q_error(self.now_date, end_date, False)) ** 2
        pprint("Error from " + str(self.now_date) + " is " + str(total_error))
        validation_file.write(" - Total Error: " + str(total_error) + "\n")
    """


    def analyze_Q_validation_files_w_intervals(self):
        files_path = get_data_location() + "Q_validation"
        validation_folders = [f for f in listdir(files_path) if os.path.isdir(join(files_path, f))]
        triplets = []
        for validation_fold in validation_folders:
            validation_files = [f for f in listdir(join(files_path,validation_fold)) if isfile(join(join(files_path,validation_fold), f))]
            x = []
            title_list = []
            episodes_map = {10: [], 20: [], 30: [], 40: [], 50: [], 60: [], 70: [], 80: [], 90: [], 100: [], 200: []}
            key = -1
            val = -1
            for validation_file_name in validation_files:
                f = open(join(join(files_path,validation_fold), validation_file_name), "r")
                title_list.append(validation_file_name)
                for line in f:
                    if "Valore Parametro" in line:
                        key = float(re.findall(r"[-+]?\d*\.\d+|\d+", line)[0])
                    elif "SSE" in line:
                        val = float(re.findall(r"[-+]?\d*\.\d+|\d+", line)[0])
                        episodes_map[key].append(val)
                f.close()
            triplet = [[], [], []]
            x_axis = []
            for key, array in episodes_map.copy().items():
                x_axis.append(key)
                triplet[1].append(np.mean(array))
                ints = self.get_confidence_interval(array)
                triplet[0].append(ints[0])
                triplet[2].append(ints[1])
            pprint(triplet)
            triplets.append(triplet)
            x = x_axis
            make_Q_validation_intervals_graph(x, triplets, title_list, "Episodes Validation SSE " + str(validation_fold))
            triplets = []

    def get_confidence_interval(self, a):
        return st.t.interval(0.95, len(a) - 1, loc=np.mean(a), scale=st.sem(a))

if __name__ == "__main__":
    sim = Simulator_RL()
    #sim.validate_n_episodes()
    #sim.validate_Q_on_episodes_number()
    #sim.analyze_Q_validation_files_w_intervals()
    sim.launch()













