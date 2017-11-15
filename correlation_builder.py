# coding=utf-8
from data_builder import *
import numpy
import math
from pprint import pprint
from os import listdir
from os.path import isfile, join
import os
import copy



#set_dirs = ["DTK", "AER", "KLD", "SOI", "EMN", "BFZ", "OGW"]
set_dirs = ["TST"]



for set_dir in set_dirs:

    if not os.path.exists(set_dir):
        os.makedirs(set_dir)
    prices_path = get_data_location() + "DATA\\MTGOprices\\Standard\\" + set_dir

    all_pearson = []
    all_pearson_s2 = []
    all_pearson_s5 = []
    all_pearson_s10 = []

    price_files = [f for f in listdir(prices_path) if isfile(join(prices_path, f))]
    for card_file in price_files:

        time_series = get_base_timeseries(set_dir, card_file, False)
        timePriceList = time_series[0]
        standardizedTourCount = time_series[1]
        if (len(standardizedTourCount) > 0):
            data = [timePriceList, standardizedTourCount]
            datatitles = ["Prices", "Usage in Tournaments", "Pearson Correlation with Shift = t"]

            shift = len(timePriceList)/5
            pearson_dict = {}
            autocorr_dict = {}

            prices = [x[1] for x in timePriceList]
            tours = [x[1] for x in standardizedTourCount]
            prices_copy = copy.deepcopy(prices)

            """calculate pearson correlation and prices autocorrelation at t0 """
            pearson_dict[0] = numpy.corrcoef(prices, tours)[0, 1]
            autocorr_dict[0] = numpy.corrcoef(prices, prices)[0, 1]
            all_pearson.append(pearson_dict[0])

            """ shift del grafico dei tornei indietro, shift dei prezzi in avanti CORRELAZIONE CON UN PREZZO PASSATO"""
            for i in range(shift):
                del tours[0]
                del prices_copy[0]
                del prices[-1]
                pearson_dict[-(i + 1)] = numpy.corrcoef(prices, tours)[0, 1]
                autocorr_dict[-(i + 1)] = numpy.corrcoef(prices, prices_copy)[0, 1]

            prices = [x[1] for x in timePriceList]
            prices_copy = copy.deepcopy(prices)
            tours = [x[1] for x in standardizedTourCount]
            """ shift del grafico dei tornei avanti, shift dei prezzi indietro CORRELAZIONE CON UN PREZZO FUTURO"""
            for i in range(shift):
                del tours[-1]
                del prices_copy[-1]
                del prices[0]
                pearson_dict[i + 1] = numpy.corrcoef(prices, tours)[0, 1]
                autocorr_dict[i + 1] = numpy.corrcoef(prices, prices_copy)[0, 1]
                if i == 1:
                    all_pearson_s2.append(pearson_dict[i + 1])
                if i == 4:
                    all_pearson_s5.append(pearson_dict[i + 1])
                if i == 9:
                    all_pearson_s10.append(pearson_dict[i + 1])


            title = os.path.splitext(card_file)[0] + "_MTGO_30d8h_MODERN"
            make_pearson_corr_graph(data, pearson_dict, autocorr_dict, datatitles, set_dir, title)

    all_pearson = [value for value in all_pearson if not math.isnan(value)]
    all_pearson_s5 = [value for value in all_pearson_s5 if not math.isnan(value)]
    all_pearson_s10 = [value for value in all_pearson_s10 if not math.isnan(value)]
    all_pearson_s2 = [value for value in all_pearson_s2 if not math.isnan(value)]

    make_pearson_histogram(all_pearson, all_pearson_s2, all_pearson_s5, all_pearson_s10, set_dir)


