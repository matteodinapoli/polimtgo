# coding=utf-8

from data_parsing.data_builder import *

from linear_regression.predictor_ARIMAX import get_ARIMAX_prediction
from linear_regression.predictor_ARIMAX import save_feature_selection_table

releases = {"AER": 1485730800000, "KLD": 1476050400000, "EMN": 1470002400000, "SOI": 1460930400000, "OGW": 1454281200000,  "BFZ": 1444600800000}

test_mode = False

#set_dirs = ["SOI", "EMN", "OGW", "BFZ", "KLD"];
set_dirs = []

""" DATA STRUCTURE """
""" {Heart of Kiran: [{prices_dict}, {predicted_dict}], Winding Constrictor: [{prices_dict}, {predicted_dict}], ...} """
data = {}
transactions = {}

""" start date of simulation """
start = "2017-01-01 20:30:55"
now_date = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
budget = 200
max_card_pieces = 20
owned_cards = {}
simulation_steps = 30
buy_threshold = 0
BH_stoploss_threshold = 0.3
BH_stopgain_threshold = 0.3


def find_current_time_key(dict, time):
    to_return =  min(dict.keys(), key=lambda x: abs(x - time) if (x - time) < datetime.timedelta(0) else 1000*abs(x - time))
    return to_return

def find_next_time_key(dict, time):
    to_return =  min(dict.keys(), key=lambda x: abs(x - time) if (x - time) > datetime.timedelta(0) else 1000*abs(x - time))
    return to_return


def get_investment_margin_list(now_date):
    margin_list = []

    for card_name, dicts_list in data.copy().items():
        current_key = find_current_time_key(dicts_list[0], now_date)
        next_key = find_next_time_key(dicts_list[1], now_date)
        if current_key in dicts_list[0]:
            today_buy_price = dicts_list[0][current_key]
            if next_key in dicts_list[1]:
                tomorrow_sell_price = dicts_list[1][next_key]
                tomorrow_sell_price_conf_10 = dicts_list[2][next_key]
                margin = tomorrow_sell_price_conf_10 - today_buy_price
                margin_list.append([card_name, margin, today_buy_price, tomorrow_sell_price, tomorrow_sell_price_conf_10])
            else:
                pprint("PREDICTION DI DOMANI " + str(next_key) + " NON PRESENTE PER " + str(card_name))
        else:
            pprint("PREZZO DI OGGI " + str(current_key) + " NON PRESENTE PER " + str(card_name))

    margin_list.sort(key=lambda x: x[1]/x[2], reverse=True)

    return margin_list


def evaluate_available_sets(now_date):
    global set_dirs
    if test_mode:
        set_dirs = ["TST"]
        return
    for set_name, timestamp in releases.copy().items():
        set_date = datetime.datetime.fromtimestamp(timestamp/1000.0)
        if now_date - set_date > datetime.timedelta(days=75):
            if set_name not in set_dirs:
                set_dirs.append(set_name)
    pprint(set_dirs)


def build_investment_map(now_date):
    evaluate_available_sets(now_date)
    for set_dir in set_dirs:

        prices_path = get_data_location() + "DATA\\MTGOprices\\Standard\\" + set_dir
        price_files = [f for f in listdir(prices_path) if isfile(join(prices_path, f))]
        for card_file in price_files:
            df_list = get_ARIMAX_prediction(set_dir, card_file, datafile, False, False, now_date, True)
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
                data[card_name] = [prices, predicted_prices, predicted_prices_10]
            else:
                if os.path.splitext(card_file)[0] in data:
                    pprint("ATTENZIONE: PREDICTION DI " + str(card_file) + " NON HA ELABORATO UN RISULTATO\n")
                    del data[os.path.splitext(card_file)[0]]
        save_feature_selection_table(set_dir)


def fill_investment_portfolio(margin_list, now_date):
    for margin_tupla in margin_list:

        card_name = margin_tupla[0]
        margin = margin_tupla[1]  #BUILT ON THE LOW CONFIDENCE INTERVAL TOMORROW SELL PRICE!
        today_buy_price = margin_tupla[2]
        tomorrow_sell_price = margin_tupla[3]

        if margin > buy_threshold + get_spread(tomorrow_sell_price):
            """ acquistiamo """
            quantity = int(budget/today_buy_price)
            if quantity > max_card_pieces:
                quantity = max_card_pieces
            if quantity > 0:
                buy_cards(card_name, quantity, today_buy_price)


def manage_owned_cards(margin_list, now_date):
    for card_name, price_key in owned_cards.copy().items():
        card_map = data[card_name]
        current_key = find_current_time_key(card_map[0], now_date)
        next_key = find_next_time_key(card_map[1], now_date)
        today_sell_price = card_map[0][current_key]
        today_sell_price -= get_spread(today_sell_price)
        tomorrow_sell_price = card_map[1][next_key]
        tomorrow_sell_price -= get_spread(tomorrow_sell_price)
        for past_price, quantity in price_key.copy().items():
            loss = past_price - today_sell_price
            loss_percentage = loss/float(past_price)
            if today_sell_price >= tomorrow_sell_price and (loss_percentage > BH_stoploss_threshold or - loss_percentage > BH_stopgain_threshold):
                sell_cards(card_name, past_price, today_sell_price)
                if card_name in transactions:
                    transactions[card_name].append([quantity, -loss])
                else:
                    transactions[card_name] = [quantity, -loss]

def sell_all_owned_cards():
    for card_name, price_key in owned_cards.copy().items():
        card_map = data[card_name]
        current_key = find_current_time_key(card_map[0], now_date)
        today_sell_price = card_map[0][current_key]
        today_sell_price -= get_spread(today_sell_price)
        for past_price, quantity in price_key.copy().items():
            loss = past_price - today_sell_price
            sell_cards(card_name, past_price, today_sell_price)
            if card_name in transactions:
                transactions[card_name].append([quantity, str(-loss)])
            else:
                transactions[card_name] = [[quantity, str(-loss)]]


def buy_cards(card_name, quantity, total_price):
    global budget
    global owned_cards
    pprint("ACQUISTO DI " + str(quantity) + " " + str(card_name) + " A " + str(total_price) + " A PEZZO")
    datafile.write("ACQUISTO DI " + str(quantity) + " " + str(card_name) + " A " + str(total_price) + " A PEZZO\n")
    budget -= quantity * total_price
    if card_name in owned_cards:
        if total_price in owned_cards[card_name]:
            owned_cards[card_name][total_price] += quantity
        else:
            owned_cards[card_name][total_price] = quantity
    else:
        x = {}
        x[total_price] = quantity
        owned_cards[card_name] = x


def sell_cards(card_name, past_buy_price, today_sell_price):
    global budget
    global owned_cards
    if today_sell_price < 0:
        today_sell_price = 0
    quantity = owned_cards[card_name][past_buy_price]
    pprint("VENDITA DI " + str(quantity) + " " + str(card_name) + " A " + str(today_sell_price) + " A PEZZO")
    datafile.write("VENDITA DI " + str(quantity) + " " + str(card_name) + " A " + str(today_sell_price) + " A PEZZO\n")
    budget += quantity * today_sell_price
    del owned_cards[card_name][past_buy_price]
    if not owned_cards[card_name]:
        del owned_cards[card_name]

def assess_portfolio(now_date):
    current_patrimony = 0
    for card_name, purchase_dict in owned_cards.copy().items():
        card_map = data[card_name]
        current_key = find_current_time_key(card_map[0], now_date)
        today_sell_price = card_map[0][current_key]
        today_sell_price -= get_spread(today_sell_price)
        for price_key, quantity in purchase_dict.copy().items():
            current_patrimony += quantity * today_sell_price
    current_patrimony += budget
    pprint("PATRIMONIO CORRENTE: " + str(current_patrimony))
    datafile.write("PATRIMONIO CORRENTE: " + str(current_patrimony) + "\n")


def get_spread(price):
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


if __name__ == "__main__":
    with open(get_data_location() + "Simulation_StopLoss5_conf10_30_30.txt", "w") as datafile:
        for step in range(simulation_steps):

            a = datetime.datetime.now()

            pprint("********** " + str(now_date) + " **********")
            datafile.write("\n\n")
            datafile.write("********** " + str(now_date) + "**********\n")

            build_investment_map(now_date)
            margin_list = get_investment_margin_list(now_date)
            manage_owned_cards(margin_list, now_date)
            if step < simulation_steps - 1:
                fill_investment_portfolio(margin_list, now_date)
            assess_portfolio(now_date)

            pprint("CARTE POSSEDUTE")
            datafile.write("CARTE POSSEDUTE\n")
            pprint(owned_cards)
            datafile.write(str(owned_cards) + "\n")
            pprint("BUDGET")
            datafile.write("BUDGET\n")
            pprint(budget)
            datafile.write(str(budget) + "\n")

            if step == simulation_steps - 1:
                sell_all_owned_cards()
                datafile.write("LISTA TRANSAZIONI\n")
                datafile.write(str(transactions) + "\n")
                datafile.write("BUDGET FINALE\n")
                datafile.write(str(budget) + "\n")

            now_date += datetime.timedelta(hours=24)

            b = datetime.datetime.now()
            delta = b - a
            pprint("STEP TIME")
            print(delta)





