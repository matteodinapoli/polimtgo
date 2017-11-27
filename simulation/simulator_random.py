from reinforcement_learning.FQI_learner import *
from simulation.simulator import Simulator
import random



class Simulator_Random(Simulator):
    test_mode = False
    start = "2017-01-01 20:30:55"
    now_date = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
    N_of_investments = 5

    def get_datafile_name(self):
        return "Simulation_RANDOM"

    def build_investment_map(self, now_date):
        self.evaluate_available_sets(now_date)
        for set_dir in self.set_dirs:
            prices_path = get_data_location() + "DATA\\MTGOprices\\Standard\\" + set_dir
            price_files = [f for f in listdir(prices_path) if isfile(join(prices_path, f))]
            for card_file in price_files:
                card_name = os.path.splitext(card_file)[0]
                """ consider only cards for which the feature selection table is defined"""
                price_list = get_prices(set_dir, card_file)
                prices_dict = {x[0]: x[1] for x in price_list}
                self.data[card_name] = prices_dict


    def get_investment_margin_list(self, now_date):
        margin_list = []
        for i in range(self.N_of_investments):
            card_name, price_dict = random.choice(list(self.data.items()))
            price_key = self.find_current_time_key(price_dict, self.now_date)
            margin_list.append([card_name, price_dict[price_key]])
        self.datafile.write(str(margin_list) + "\n")
        return margin_list


    def fill_investment_portfolio(self, margin_list, now_date):
        for margin_tupla in margin_list:
            card_name = margin_tupla[0]
            today_buy_price = margin_tupla[1]
            quantity = int(self.budget / today_buy_price)
            if quantity > self.max_card_pieces:
                quantity = self.max_card_pieces
            if quantity > 0:
                self.buy_cards(card_name, quantity, today_buy_price)


    def manage_owned_cards(self, margin_list, now_date):
        for card_name, price_key in self.owned_cards.copy().items():

            today_sell_price = self.get_price_from_data_map(card_name)

            for past_price, quantity in price_key.copy().items():
                gain = today_sell_price - past_price
                gain_percentage = gain / float(past_price)
                if gain_percentage > self.BH_stopgain_threshold:
                    self.sell_cards(card_name, past_price, today_sell_price)
                    if card_name in self.transactions:
                        self.transactions[card_name].append([quantity, gain])
                    else:
                        self.transactions[card_name] = [quantity, gain]


    def get_price_from_data_map(self, card_name):
        price_dict = self.data[card_name]
        price_key = self.find_current_time_key(price_dict, self.now_date)
        price = price_dict[price_key]
        price -= get_spread(price)
        return price




if __name__ == "__main__":
    sim = Simulator_Random()
    sim.launch()
















