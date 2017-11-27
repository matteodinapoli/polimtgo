import json
import collections
import operator
from os import listdir
from os.path import isfile, join
from dateutil import parser
import datetime
from pprint import pprint
import copy

""" numero di tornei presi in considerazione per la media degli ultimi tornei"""
considered_tours = 3
""" orizzonte temporale preso in considerazione per la media pesata dei tornei in questo lasso di tempo """
considered_days = 30
discount_factor = 0.8

tour_date_count_map = {}



def get_data_location():
    return "C:\\Users\\pitu\\Desktop\\"


def get_tournament_card_count(path):
    with open(path) as datafile:
        raw_tour = json.load(datafile)
    decks = raw_tour["decks"]
    cards = []
    card_count_dict = {}
    for deck in decks:
        cards.append(deck["cards"])
        cards.append(deck["sideboard"])
    for deckCards in cards:
        for tupla_card in deckCards:
            name = tupla_card["name"]
            if name in card_count_dict:
                card_count_dict[name] += tupla_card["count"]
            else:
                card_count_dict[name] = tupla_card["count"]
    sorted_card_count = collections.OrderedDict(sorted(card_count_dict.items(), key=operator.itemgetter(1), reverse=True))
    return sorted_card_count


def get_tournament_date(path):
    with open(path) as datafile:
        raw_tour = json.load(datafile)
    date = raw_tour["date"]
    date_time = parser.parse(date[0:-1])
    return date_time

def get_budget_date(path):
    with open(path) as datafile:
        raw_tour = json.load(datafile)
    date = raw_tour["date"]
    date_time = parser.parse(date)
    return date_time


def clean_prices_before_any_tournament (prices_dict, tour_dict):
    for datePrice in prices_dict.keys():
        if datePrice not in tour_dict.keys():
            #pricesDict.pop(datePrice)
            tour_dict[datePrice] = 0


def build_tournament_history(card, avg, time, onlyMTGO, first_price_date):

    tfiles = []

    if onlyMTGO:
        mtgo_path = get_data_location() + "DATA\\PRO_Tournaments\\MTGO_standard"
        #mtgo_path = get_data_location() + "DATA\\PRO_Tournaments\\MTGO_modern"
        mtgo_files = [f for f in listdir(mtgo_path) if isfile(join(mtgo_path, f))]
        for league in mtgo_files:
            tfiles.append(join(mtgo_path, league))

    else:
        tour_path = get_data_location() + "DATA\\PRO_Tournaments\\PT"
        tour_files = [f for f in listdir(tour_path) if isfile(join(tour_path, f))]

        gp_path = get_data_location() + "DATA\\PRO_Tournaments\\GP"
        gp_files = [f for f in listdir(gp_path) if isfile(join(gp_path, f))]

        twos_path = get_data_location() + "DATA\\PRO_Tournaments\\2stars"
        twos_files = [f for f in listdir(twos_path) if isfile(join(twos_path, f))]


        for pt in tour_files:
            tfiles.append(join(tour_path, pt))
        for gp in gp_files:
            tfiles.append(join(gp_path, gp))
        for t in twos_files:
            tfiles.append(join(twos_path, t))

    return build_history(tfiles, card, avg, time, False, "usage", first_price_date)



def build_modern_history(card, avg, time, first_price_date):

    tfiles = []
    mtgo_path = get_data_location() + "DATA\\PRO_Tournaments\\MTGO_modern"
    mtgo_files = [f for f in listdir(mtgo_path) if isfile(join(mtgo_path, f))]
    for league in mtgo_files:
        tfiles.append(join(mtgo_path, league))
    return build_history(tfiles, card, avg, time, False, "modern", first_price_date)


def build_pt_history(card, first_price_date):

    tfiles = []
    mtgo_path = get_data_location() + "DATA\\PRO_Tournaments\\PT"
    mtgo_files = [f for f in listdir(mtgo_path) if isfile(join(mtgo_path, f))]
    for league in mtgo_files:
        tfiles.append(join(mtgo_path, league))
    return build_history(tfiles, card, False, False, False, "ptExps", first_price_date)


def build_budget_history(card, avg, time, first_price_date):

    tfiles = []
    mtgo_path = get_data_location() + "DATA\\BUDGET_MAGIC"
    mtgo_files = [f for f in listdir(mtgo_path) if isfile(join(mtgo_path, f))]
    for league in mtgo_files:
        tfiles.append(join(mtgo_path, league))
    return build_history(tfiles, card, avg, time, True, "budget", first_price_date)

def build_all_goldfish_history(card, avg, time, first_price_date):

    tfiles = []
    mtgo_path = get_data_location() + "DATA\\ALL_GOLDFISH"
    mtgo_files = [f for f in listdir(mtgo_path) if isfile(join(mtgo_path, f))]
    for league in mtgo_files:
        tfiles.append(join(mtgo_path, league))
    return build_history(tfiles, card, avg, time, True, "allG", first_price_date)



def build_history(tfiles, card, avg, time, budget, kind, first_price_date):
    tour_date_count = []

    if kind not in tour_date_count_map:
        tour_date_count_map[kind] = {}
    if card in tour_date_count_map[kind]:
        tour_date_count = tour_date_count_map[kind][card]
    else:
        for tournament in tfiles:
            if budget:
                tour_date = get_budget_date(tournament)
            else:
                tour_date = get_tournament_date(tournament)
            if tour_date > first_price_date:
                tour_cards = get_tournament_card_count(tournament)
                if card in tour_cards:
                    tour_date_count.append([tour_date, tour_cards[card]])
                else:
                    tour_date_count.append([tour_date, 0])

        tour_date_count.sort(key=lambda x: x[0])
        pos = 0
        """ considero la media degli ultimi #considered_tours# tornei """
        if avg:
            copy_list = copy.deepcopy(tour_date_count)
            for date_num in tour_date_count:
                avg_val = []
                for j in range(pos, pos - considered_tours, -1):
                    if j >= 0:
                        avg_val.append(copy_list[j][1])
                date_num[1] = (sum(avg_val) / float(len(avg_val)))
                pos += 1
        elif time:
            """ costruisco una media pesata di tutti gli ultimi tornei presenti nell'arco di #considered_days, con
                 discount factor esponenziale gamma moltiplicato per i valori via via piu lontani """
            extend_timeseries_w_gamma(tour_date_count, discount_factor)

        tour_date_count_map[kind][card] = tour_date_count

    return tour_date_count



def extend_timeseries_w_gamma(timeseries, discount_factor):
    copy_list = copy.deepcopy(timeseries)
    for date_num in timeseries:
        lookback_list = []
        lookback_list.append(date_num[1])
        i = timeseries.index(date_num) - 1
        weight = 1
        gamma = discount_factor
        while i >= 0 and (date_num[0] - copy_list[i][0]).days < considered_days:
            lookback_list.append(gamma * copy_list[i][1])
            weight = weight + gamma
            gamma = gamma * discount_factor
            i = i - 1
        res = (sum(lookback_list) / float(weight))
        if abs(res) < 0.05:
            res = 0
        date_num[1] = res
