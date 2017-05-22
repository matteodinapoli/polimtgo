# coding=utf-8
import datetime
from TournamentReader import *
from GraphMaker import *
import numpy
from pprint import pprint
from os import listdir
from os.path import isfile, join
import os


set_dir = "BFZ"

if not os.path.exists(set_dir):
    os.makedirs(set_dir)
prices_path = "MTGOprices\\Standard\\" + set_dir

price_files = [f for f in listdir(prices_path) if isfile(join(prices_path, f))]
for card_file in price_files:
    with open("MTGOprices\\Standard\\" + set_dir + "\\" + card_file) as datafile:
        rawjson = json.load(datafile)
    timePriceList = rawjson["data"]


    """ datePrices: dizionario --> data = prezzo """
    datePrices = {}
    for tupla in timePriceList:
        datePrices[datetime.datetime.fromtimestamp(tupla[0]/1000.0)] = tupla[1]


    """ tourDateCount: dizionario --> data torneo = numero di quella carta in top8 """
    tourDateCount = build_tournament_history(os.path.splitext(card_file)[0])
    if len(tourDateCount) > 0:

        """ costruisco standardizedTourCount, un dizionario in cui ad ogni giorno (date prese da quelle del dizionario dei prezzi,
        aggiornato giorno per giorno) associo l'uso di quella carta nel torneo più recente """
        standardizedTourCount = {}
        for datePrice in datePrices.keys():
            closerDate = datetime.datetime(1970,1,1)
            for dateTour in tourDateCount.keys():
                if datePrice > dateTour and datePrice - dateTour < datePrice - closerDate:
                    closerDate = dateTour
                    standardizedTourCount[datePrice] = tourDateCount[dateTour]


        """ aggiungo valori a zero per dare lo stesso dominio ai due dizionari"""
        clean_prices_before_any_tournament(datePrices, standardizedTourCount)


        data = [datePrices, standardizedTourCount]
        datatitles = ["Prices", "Usage in Tournaments", "Pearson Correlation with Shift = t"]


        shift = len(datePrices)/4
        pearson_dict = {}
        sortDatePrices = sorted(datePrices.items())
        sortTourCount = sorted(standardizedTourCount.items())
        x_p, y_p = zip(*sortDatePrices)
        x_t, y_t = zip(*sortTourCount)
        pearson_dict[0] = numpy.corrcoef(y_p, y_t)[0, 1]

        """ shift del grafico dei tornei indietro, shift dei prezzi in avanti """
        for i in xrange(shift):
            del sortTourCount[0]
            del sortDatePrices[-1]
            x_p, y_p = zip(*sortDatePrices)
            x_t, y_t = zip(*sortTourCount)
            pearson_dict[i + 1] = numpy.corrcoef(y_p, y_t)[0, 1]

        sortDatePrices = sorted(datePrices.items())
        sortTourCount = sorted(standardizedTourCount.items())
        """ shift del grafico dei tornei avanti, shift dei prezzi indietro """
        for i in xrange(shift):
            del sortTourCount[-1]
            del sortDatePrices[0]
            x_p, y_p = zip(*sortDatePrices)
            x_t, y_t = zip(*sortTourCount)
            pearson_dict[- (i + 1)] = numpy.corrcoef(y_p, y_t)[0, 1]

        make_pearson_corr_graph(data, pearson_dict, datatitles, set_dir, os.path.splitext(card_file)[0])




