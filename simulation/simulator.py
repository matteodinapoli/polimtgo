# coding=utf-8

from data_parsing.data_builder import *
import re
import pathlib as pb

class Simulator:
    iteration = 1

    releases = {"TST":1444600800000, "AER": 1485730800000, "KLD": 1476050400000, "EMN": 1470002400000, "SOI": 1460930400000, "OGW": 1454281200000,  "BFZ": 1444600800000}

    starts = ["2016-04-01 20:30:55", "2016-06-01 20:30:55", "2016-08-01 20:30:55", "2016-10-01 20:30:55", "2016-12-01 20:30:55", "2017-02-01 20:30:55"]
    #starts = ["2016-04-01 20:30:55", "2016-07-01 20:30:55", "2016-10-01 20:30:55", "2017-01-01 20:30:55"]

    test_mode = False
    set_dirs = []
    data = {}
    transactions = {}

    starting_budget = 2000
    budget = 2000
    max_card_pieces = 20
    owned_cards = {}
    simulation_steps = 90
    buy_threshold = 0
    BH_stoploss_threshold_l = [0, 0.2, 0.4, 0.6, 0.8]
    BH_stopgain_threshold_l = [0, 0.2, 0.4, 0.6, 0.8]
    BH_stoploss_threshold = 0
    BH_stopgain_threshold = 0
    datafile = None

    """ for cross-validation """
    episodes_n = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 1000]
    actual_episodes_n = 200
    results_episodes = {10: [], 20: [], 30: [], 40: [], 50: [], 60: [], 70: [], 80: [], 90: [], 100: [], 200: [], 300: [], 400: [], 500: [], 600: [], 700: [], 800: [], 900: [], 1000: []}


    def init_params_for_validation(self):
        self.BH_stoploss_threshold_l = [0]
        self.BH_stopgain_threshold_l = [0]
        self.budget = 1000
        self.starting_budget = 1000
        self.simulation_steps = 180

    def find_current_time_key(self, dict, time):
        to_return =  min(dict.keys(), key=lambda x: abs(x - time) if (x - time) < datetime.timedelta(0) else 1000*abs(x - time))
        return to_return

    def find_next_time_key(self, dict, time):
        to_return =  min(dict.keys(), key=lambda x: abs(x - time) if (x - time) > datetime.timedelta(0) else 1000*abs(x - time))
        return to_return

    def evaluate_available_sets(self):
        if self.test_mode:
            self.set_dirs = ["TST"]
            return
        for set_name, timestamp in releases.copy().items():
            set_date = datetime.datetime.fromtimestamp(timestamp/1000.0)
            if self.now_date - set_date > datetime.timedelta(days=75):
                if set_name not in self.set_dirs:
                    self.set_dirs.append(set_name)
        pprint(self.set_dirs)

    def sell_all_owned_cards(self):
        for card_name, price_key in self.owned_cards.copy().items():
            today_sell_price = self.get_price_from_data_map(card_name)
            for past_price, quantity in price_key.copy().items():
                loss = past_price - today_sell_price
                self.sell_cards(card_name, past_price, today_sell_price)
                if card_name in self.transactions:
                    self.transactions[card_name].append( [quantity, -loss] )
                else:
                    self.transactions[card_name] = [ [quantity, -loss] ]

    def buy_cards(self, card_name, quantity, total_price):
        pprint("ACQUISTO DI " + str(quantity) + " " + str(card_name) + " A " + str(total_price) + " A PEZZO")
        self.datafile.write("ACQUISTO DI " + str(quantity) + " " + str(card_name) + " A " + str(total_price) + " A PEZZO\n")
        self.budget -= quantity * total_price
        if card_name in self.owned_cards:
            if total_price in self.owned_cards[card_name]:
                self.owned_cards[card_name][total_price] += quantity
            else:
                self.owned_cards[card_name][total_price] = quantity
        else:
            x = {}
            x[total_price] = quantity
            self.owned_cards[card_name] = x

    def sell_cards(self, card_name, past_buy_price, today_sell_price):
        if today_sell_price < 0:
            today_sell_price = 0
        quantity = self.owned_cards[card_name][past_buy_price]
        pprint("VENDITA DI " + str(quantity) + " " + str(card_name) + " A " + str(today_sell_price) + " A PEZZO")
        self.datafile.write("VENDITA DI " + str(quantity) + " " + str(card_name) + " A " + str(today_sell_price) + " A PEZZO\n")
        gain = quantity * (today_sell_price - past_buy_price)
        if gain > 0:
            self.datafile.write("# Transazione Positiva, Guadagno: " + str(gain) + "\n")
        else:
            self.datafile.write("* Transazione Negativa, Perdita: " + str(gain) + "\n")
        self.budget += quantity * today_sell_price
        del self.owned_cards[card_name][past_buy_price]
        if not self.owned_cards[card_name]:
            del self.owned_cards[card_name]

    def assess_portfolio(self):
        current_patrimony = 0
        for card_name, purchase_dict in self.owned_cards.copy().items():
            today_sell_price = self.get_price_from_data_map(card_name)
            for price_key, quantity in purchase_dict.copy().items():
                current_patrimony += quantity * today_sell_price
        current_patrimony += self.budget
        pprint("PATRIMONIO CORRENTE: " + str(current_patrimony))
        self.datafile.write("PATRIMONIO CORRENTE: " + str(current_patrimony) + "\n")

    def get_spread(self, price):
        if 0 <= price < 0.07:
            return 0.03
        elif 0.07 <= price < 0.15:
            return 0.04
        elif 0.15 <= price < 0.23:
            return 0.06
        elif 0.23 <= price < 0.29:
            return 0.08
        elif 0.29 <= price < 0.39:
            return 0.10
        elif 0.39 <= price < 0.86:
            return 0.13
        elif 0.86 <= price < 0.89:
            return 0.15
        elif 0.89 <= price < 2.34:
            return 0.18
        elif 2.34 <= price < 3.29:
            return 0.23
        elif 3.29 <= price < 5.04:
            return 0.28
        elif 5.04 <= price < 6.39:
            return 0.33
        elif 6.39 <= price < 8.09:
            return 0.38
        elif 8.09 <= price < 10.09:
            return 0.43
        elif 10.09 <= price < 12.24:
            return 0.48
        elif 12.24 <= price < 15.78:
            return 0.58
        elif 15.78 <= price < 19.08:
            return 0.68
        elif 19.08 <= price < 21.08:
            return 0.78
        elif 21.08 <= price < 22.36:
            return 0.88
        elif 22.36 <= price < 25.36:
            return 0.98
        elif 25.36 <= price < 29.36:
            return 1.08
        elif 29.36 <= price < 35.36:
            return 1.18
        elif 35.36 <= price < 39.36:
            return 1.38
        elif 39.36 <= price < 43.36:
            return 1.58
        elif 43.36 <= price < 46.87:
            return 1.78
        elif 46.87 <= price < 51.86:
            return 1.98
        return price * 0.05


    def aggregate_simulation_results(self):
        files_path = get_data_location() + self.get_result_folder()
        types = ["0_0.txt", "0.2_0.2.txt", "0.4_0.4.txt", "0.6_0.6.txt", "0.8_0.8.txt"]
        budgets = ["B500_", "B1000_", "B2000_", "B5000_"]
        validation_files = [f for f in listdir(files_path) if isfile(join(files_path, f))]
        for budget in budgets:
            for type in types:
                final_results = []
                for validation_file_name in validation_files:
                    if type in validation_file_name and budget in validation_file_name:
                        f = open(join(files_path, validation_file_name), "r")
                        value = False
                        for line in f:
                            if "BUDGET FINALE" in line:
                                value = True
                            elif value:
                                final_results.append(float(re.findall(r"[-+]?\d*\.\d+|\d+", line)[0]))
                                value = False
                        f.close()
                if final_results:
                    with open(get_data_location() + self.get_result_folder() + "Aggregated_Result_" + budget + "_" + type, "w") as result_file:
                        avg = np.average(final_results)
                        result_file.write("Average Result: " + str(avg) + "\n")
                        variance = np.var(final_results)
                        result_file.write("Result Variance: " + str(variance) + "\n")
                        std = np.std(final_results)
                        result_file.write("Result Standard Deviation: " + str(std) + "\n")



    def launch(self):
        for stoploss in self.BH_stoploss_threshold_l:
            self.BH_stoploss_threshold = stoploss
            for stopgain in self.BH_stopgain_threshold_l:
                self.BH_stopgain_threshold = stopgain
                if self.BH_stoploss_threshold == self.BH_stopgain_threshold:
                    self.now_date = datetime.datetime.strptime(self.start, "%Y-%m-%d %H:%M:%S")
                    self.owned_cards.clear()
                    self.budget = self.starting_budget
                    self.transactions = {}
                    self.set_dirs = []
                    pprint("********** SIMULATION START **********")
                    with open(get_data_location()+ self.get_result_folder() + self.get_datafile_name() + "_" + str(self. BH_stoploss_threshold) + "_" + str(self.BH_stopgain_threshold) + ".txt", "w") as self.datafile:
                        for step in range(self.simulation_steps):

                            pprint("********** " + str(self.now_date) + " **********")
                            self.datafile.write("\n\n")
                            self.datafile.write("********** " + str(self.now_date) + "**********\n")

                            self.build_investment_map()
                            self.datafile.write(str(self.set_dirs))
                            margin_list = self.get_investment_margin_list()
                            self.manage_owned_cards(margin_list)
                            if step < self.simulation_steps - 1:
                                self.fill_investment_portfolio(margin_list)
                            self.assess_portfolio()

                            pprint("CARTE POSSEDUTE")
                            self.datafile.write("CARTE POSSEDUTE\n")
                            pprint(self.owned_cards)
                            self.datafile.write(str(self.owned_cards) + "\n")
                            pprint("BUDGET")
                            self.datafile.write("BUDGET\n")
                            pprint(self.budget)
                            self.datafile.write(str(self.budget) + "\n")

                            if step == self.simulation_steps - 1:
                                self.sell_all_owned_cards()
                                self.datafile.write("LISTA TRANSAZIONI\n")
                                self.datafile.write(str(self.transactions) + "\n")
                                pos = 0
                                pos_n = 0
                                neg = 0
                                neg_n = 0
                                for card, list in self.transactions.copy().items():
                                    for tupla in list:
                                        gain = tupla[1] * tupla[0]
                                        if gain > 0:
                                            pos += gain
                                            pos_n += 1
                                        else:
                                            neg += gain
                                            neg_n += 1
                                self.results_episodes[self.actual_episodes_n].append([self.budget, pos_n, pos, neg_n, neg])
                                self.datafile.write("Transazioni positive: " + str(pos_n)  +"\n")
                                self.datafile.write("Guadagno totale: " + str(pos) + "\n")
                                self.datafile.write("Transazioni negative: " + str(neg_n) + "\n")
                                self.datafile.write("Perdita totale: " + str(neg) + "\n")
                                self.datafile.write(str(self.transactions) + "\n")
                                self.datafile.write("BUDGET FINALE\n")
                                self.datafile.write(str(self.budget) + "\n")

                            self.now_date += datetime.timedelta(hours=24)



    """ TO BE IMPLEMENTED IN SUBCLASSES """

    def build_investment_map(self):
        return

    def get_investment_margin_list(self, now_date):
        return

    def fill_investment_portfolio(self, margin_list, now_date):
        return

    def manage_owned_cards(self, margin_list, now_date):
        return

    def get_price_from_data_map(self, card_name):
        return

    def get_datafile_name(self):
        return

    def get_result_folder(self):
        return "SIM\\"

