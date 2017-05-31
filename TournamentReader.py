import json
import collections
import operator
from os import listdir
from os.path import isfile, join
from dateutil import parser
from pprint import pprint


considered_tours = 5


def get_tournament_card_count(path):
    with open(path) as datafile:
        raw_tour = json.load(datafile)
    decks = raw_tour["decks"]
    cards = []
    card_count_dict = {}
    for deck in decks:
        cards.append(deck["cards"])
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


def clean_prices_before_any_tournament (prices_dict, tour_dict):
    for datePrice in prices_dict.keys():
        if datePrice not in tour_dict.keys():
            #pricesDict.pop(datePrice)
            tour_dict[datePrice] = 0


def build_tournament_history(card, avg, onlyMTGO):

    tfiles = []

    if onlyMTGO:
        mtgo_path = "C:\\Users\\pitu\\Desktop\\DATA\\PRO_Tournaments\\Competitive_cleaned"
        mtgo_files = [f for f in listdir(mtgo_path) if isfile(join(mtgo_path, f))]
        for league in mtgo_files:
            tfiles.append(join(mtgo_path, league))

    else:
        tour_path = "C:\\Users\\pitu\\Desktop\\DATA\\PRO_Tournaments\\PT"
        tour_files = [f for f in listdir(tour_path) if isfile(join(tour_path, f))]

        gp_path = "C:\\Users\\pitu\\Desktop\\DATA\\PRO_Tournaments\\GP"
        gp_files = [f for f in listdir(gp_path) if isfile(join(gp_path, f))]

        twos_path = "C:\\Users\\pitu\\Desktop\\DATA\\PRO_Tournaments\\2stars"
        twos_files = [f for f in listdir(twos_path) if isfile(join(twos_path, f))]


        for pt in tour_files:
            tfiles.append(join(tour_path, pt))
        for gp in gp_files:
            tfiles.append(join(gp_path, gp))
        for t in twos_files:
            tfiles.append(join(twos_path, t))

    tour_date_count = {}

    for tournament in tfiles:
        tour_cards = get_tournament_card_count(tournament)
        tour_date = get_tournament_date(tournament)
        if card in tour_cards:
            tour_date_count[tour_date] = tour_cards[card]
        else:
            tour_date_count[tour_date] = 0

    pos = 0
    if avg:
        ord_tour = sorted(tour_date_count.items())
        avg_tour = {}
        for i in ord_tour:
            avg_val = []
            for j in xrange(pos, pos - considered_tours, -1):
                if j >= 0:
                    avg_val.append(ord_tour[j][1])
            avg_tour[ord_tour[pos][0]] = (sum(avg_val) / float(len(avg_val)))
            pos += 1
        return avg_tour
    else:
        return tour_date_count
