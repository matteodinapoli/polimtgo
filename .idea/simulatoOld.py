# coding=utf-8
from data_builder import *
from datetime import datetime
from predictor_ARIMAX import *
from os import listdir
from os.path import isfile, join
import os
import pandas as pd
import pyflux as pf
import numpy as np
import bisect

start_double = "2017-01-11 18:30:55"
double_date = datetime.datetime.strptime(start_double, "%Y-%m-%d %H:%M:%S")

set_dirs = ["SOI", "EMN", "OGW", "BFZ", "KLD"];
#set_dirs = ["TST"]

""" DATA STRUCTURE """
""" {Heart of Kiran: [{prices_dict}, {predicted_dict}], Winding Constrictor: [{prices_dict}, {predicted_dict}], ...} """
data = {}

""" start date of simulation """
start = "2017-01-01 20:30:55"
now_date = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
budget = 200
max_card_pieces = 20
owned_cards = {}
simulation_steps = 60


def find_current_time_key(dict, time):
    to_return =  min(dict.keys(), key=lambda x: abs(x - time) if (x - time) < datetime.timedelta(0) else 1000*abs(x - time))
    return to_return


def find_next_time_key(dict, time):
    to_return =  min(dict.keys(), key=lambda x: abs(x - time) if (x - time) > datetime.timedelta(0) else 1000*abs(x - time))
    return to_return


def get_investment_margin_list(now_date):
    margin_list = []

    for card_name, dicts_list in data.items():
        current_key = find_current_time_key(dicts_list[0], now_date)
        next_key = find_next_time_key(dicts_list[1], now_date)
        if current_key in dicts_list[0]:
            today_buy_price = dicts_list[0][current_key]
            if next_key in dicts_list[1]:
                tomorrow_sell_price = dicts_list[1][next_key]
                margin = tomorrow_sell_price - today_buy_price
                margin_list.append([card_name, margin, today_buy_price])
            else:
                pprint("PREDICTION DI DOMANI " + str(next_key) + " NON PRESENTE PER " + str(card_name))
        else:
            pprint("PREZZO DI OGGI " + str(current_key) + " NON PRESENTE PER " + str(card_name))

    margin_list.sort(key=lambda x: x[1]/x[2], reverse=True)

    return margin_list


def build_investment_map():
    for set_dir in set_dirs:

        if not os.path.exists(set_dir):
            os.makedirs(set_dir)
        prices_path = get_data_location() + "DATA\\MTGOprices\\Standard\\" + set_dir
        price_files = [f for f in listdir(prices_path) if isfile(join(prices_path, f))]
        for card_file in price_files:

            df_list = get_ARIMAX_prediction(set_dir, card_file, datafile, False, False, now_date, True)
            if df_list is not None:
                df = df_list[0]
                predicted_df = df_list[1]
                prices_raw = df.ix[-2:]['prices'].to_dict()
                prices = {key.to_datetime().replace(minute=0, second=0, microsecond=0): val for key, val in prices_raw.items()}
                predicted_prices_raw = predicted_df['prices'].to_dict()
                predicted_prices = {key.to_datetime().replace(minute=0, second=0, microsecond=0) : val for key, val in predicted_prices_raw.items()}
                data[os.path.splitext(card_file)[0]] = [prices, predicted_prices]
            else:
                if os.path.splitext(card_file)[0] in data:
                    pprint("ATTENZIONE: PREDICTION DI " + str(card_file) + " NON HA ELABORATO UN RISULTATO\n")
                    del data[os.path.splitext(card_file)[0]]


def fill_investment_portfolio(margin_list, now_date):
    for margin_tupla in margin_list:

        card_name = margin_tupla[0]
        margin = margin_tupla[1]
        today_buy_price = margin_tupla[2]
        spread = get_spread(today_buy_price)
        total_price = today_buy_price + spread

        if margin > spread:
            """ acquistiamo """
            quantity = int(budget/total_price)
            if quantity > max_card_pieces:
                quantity = max_card_pieces
            if quantity > 0:
                buy_cards(card_name, quantity, total_price)


def manage_owned_cards(margin_list, now_date):
    for card_name, quantity in owned_cards.items():
        card_map = data[card_name]
        current_key = find_current_time_key(card_map[0], now_date)
        next_key = find_next_time_key(card_map[1], now_date)
        today_sell_price = card_map[0][current_key]
        tomorrow_sell_price = card_map[1][next_key]
        if today_sell_price >= tomorrow_sell_price:
            sell_cards(card_name, today_sell_price)


def sell_all_owned_cards():
    for card_name, quantity in owned_cards.items():
        card_map = data[card_name]
        current_key = find_current_time_key(card_map[0], now_date)
        today_sell_price = card_map[0][current_key]
        sell_cards(card_name, today_sell_price)


def buy_cards(card_name, quantity, total_price):
    global budget
    global owned_cards
    pprint("ACQUISTO DI " + str(quantity) + " " + str(card_name) + " A " + str(total_price) + " A PEZZO")
    datafile.write("ACQUISTO DI " + str(quantity) + " " + str(card_name) + " A " + str(total_price) + " A PEZZO\n")
    budget -= quantity * total_price
    if card_name in owned_cards:
        owned_cards[card_name] += quantity
    else:
        owned_cards[card_name] = quantity


def sell_cards(card_name, today_sell_price):
    global budget
    global owned_cards
    quantity = owned_cards[card_name]
    pprint("VENDITA DI " + str(quantity) + " " + str(card_name) + " A " + str(today_sell_price) + " A PEZZO")
    datafile.write("VENDITA DI " + str(quantity) + " " + str(card_name) + " A " + str(today_sell_price) + " A PEZZO\n")
    budget += quantity * today_sell_price
    del owned_cards[card_name]


def assess_portfolio(now_date):
    current_patrimony = 0
    for card_name, quantity in owned_cards.items():
        card_map = data[card_name]
        current_key = find_current_time_key(card_map[0], now_date)
        today_sell_price = card_map[0][current_key]
        today_sell_price -= get_spread(today_sell_price)
        current_patrimony += quantity * today_sell_price
    current_patrimony += budget
    pprint("PATRIMONIO CORRENTE: " + str(current_patrimony))
    datafile.write("PATRIMONIO CORRENTE: " + str(current_patrimony) + "\n")


def get_spread(price):
    spread = price*0.1
    if spread < 0.05: spread = 0.05
    return spread


with open(get_data_location() + "SimulationOld_OldSpread.txt", "w") as datafile:
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
            datafile.write("BUDGET FINALE\n")
            datafile.write(str(budget) + "\n")

        now_date += datetime.timedelta(hours=24)

        b = datetime.datetime.now()
        delta = b - a
        pprint("STEP TIME")
        print delta




