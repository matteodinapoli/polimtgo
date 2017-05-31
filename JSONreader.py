# coding=utf-8
import datetime
from TournamentReader import *
from GraphMaker import *
import numpy
import math
from pprint import pprint
from os import listdir
from os.path import isfile, join
import os


set_dirs = ["AER", "KLD", "SOI", "EMN", "BFZ", "OGW"]
avg = True
onlyMTGO = True
cut_start = True
cut_size = 30


for set_dir in set_dirs:

    if not os.path.exists(set_dir):
        os.makedirs(set_dir)
    prices_path = "C:\\Users\\pitu\\Desktop\\DATA\\MTGOprices\\Standard\\" + set_dir

    all_pearson = []
    all_pearson_s5 = []
    all_pearson_s10 = []
    all_pearson_s20 = []

    price_files = [f for f in listdir(prices_path) if isfile(join(prices_path, f))]
    for card_file in price_files:
        with open("C:\\Users\\pitu\\Desktop\\DATA\\MTGOprices\\Standard\\" + set_dir + "\\" + card_file) as datafile:
            rawjson = json.load(datafile)
        timePriceList = rawjson["data"]

        """remove prices of the first 15 days due to the high frequency"""
        if cut_start:
            timePriceList = timePriceList[cut_size:]

        """ datePrices: dizionario --> data = prezzo """
        datePrices = {}
        for tupla in timePriceList:
            datePrices[datetime.datetime.fromtimestamp(tupla[0]/1000.0)] = tupla[1]


        """ tourDateCount: dizionario --> data torneo = numero di quella carta in top8 """
        tourDateCount = build_tournament_history(os.path.splitext(card_file)[0], avg, onlyMTGO)

        checkmax_list = tourDateCount.values()
        max_val = max(checkmax_list)

        if len(tourDateCount) > 0 and max_val >= 1:
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

            shift = len(datePrices)/5
            pearson_dict = {}
            sortDatePrices = sorted(datePrices.items())
            sortTourCount = sorted(standardizedTourCount.items())
            x_p, y_p = zip(*sortDatePrices)
            x_t, y_t = zip(*sortTourCount)
            pearson_dict[0] = numpy.corrcoef(y_p, y_t)[0, 1]
            all_pearson.append(pearson_dict[0])

            """ shift del grafico dei tornei indietro, shift dei prezzi in avanti CORRELAZIONE CON UN PREZZO PASSATO"""
            for i in xrange(shift):
                del sortTourCount[0]
                del sortDatePrices[-1]
                x_p, y_p = zip(*sortDatePrices)
                x_t, y_t = zip(*sortTourCount)
                pearson_dict[-(i + 1)] = numpy.corrcoef(y_p, y_t)[0, 1]


            sortDatePrices = sorted(datePrices.items())
            sortTourCount = sorted(standardizedTourCount.items())
            """ shift del grafico dei tornei avanti, shift dei prezzi indietro CORRELAZIONE CON UN PREZZO FUTURO"""
            for i in xrange(shift):
                del sortTourCount[-1]
                del sortDatePrices[0]
                x_p, y_p = zip(*sortDatePrices)
                x_t, y_t = zip(*sortTourCount)
                pearson_dict[i + 1] = numpy.corrcoef(y_p, y_t)[0, 1]
                if i == 4:
                    all_pearson_s5.append(pearson_dict[i + 1])
                if i == 9:
                    all_pearson_s10.append(pearson_dict[i + 1])
                if i == 19:
                    all_pearson_s20.append(pearson_dict[i + 1])

            if cut_start:
                title = os.path.splitext(card_file)[0] + "_MTGO_cut"
            elif onlyMTGO:
                title = os.path.splitext(card_file)[0] + "_MTGOgt1"
            elif avg:
                title = os.path.splitext(card_file)[0] + "_avg5"
            else:
                title = os.path.splitext(card_file)[0]
            make_pearson_corr_graph(data, pearson_dict, datatitles, set_dir, title)


    all_pearson = [value for value in all_pearson if not math.isnan(value)]
    all_pearson_s5 = [value for value in all_pearson_s5 if not math.isnan(value)]
    all_pearson_s10 = [value for value in all_pearson_s10 if not math.isnan(value)]
    all_pearson_s20 = [value for value in all_pearson_s20 if not math.isnan(value)]

    make_pearson_histogram(all_pearson, all_pearson_s5, all_pearson_s10, all_pearson_s20, set_dir)


