# coding=utf-8
import os

from data_parsing.tournament_reader import *
from graphics.graph_maker import *
from linear_regression.predictor_ARIMAX import *

""" make backward-average of tournament data"""
average = False
""" consider a backward time-horizon of tournament data with discount factor"""
time = True

onlyMTGO = True
""" remove from prices first n data due to high frequency"""
cut_start = True
cut_size = 30

"use differencing on average of n previous values on both timeseries"
derivative = False
deriv_avg_n = 5


releases = {"AER": 1485730800000, "KLD": 1476050400000, "EMN": 1470002400000, "SOI": 1460930400000, "OGW": 1454281200000,  "BFZ": 1444600800000}
card_count = {"AER": 184, "KLD": 264, "EMN": 205, "SOI": 297, "OGW": 184,  "BFZ": 274}
set_dirs = ["SOI", "EMN", "OGW", "BFZ", "KLD", "AER"];
standard_exit = {"DTK": 1476050400000}

feature_to_index_table = {"prices": 0, "usage": 1, "budget": 2, "packs": 3, "exit": 4, "allG": 5, "ptExps": 6, "modern": 7, "MACD": 8, "RSI": 9}
total_market_price = {}
total_price_MACD = None



def get_feature_to_index_map():
    return feature_to_index_table


def get_total_market_price_MACD():
    global total_price_MACD
    if not total_price_MACD:
        build_total_market_price_map()
        market_price_list = []
        for key, value in total_market_price.copy().items():
            avg = value[1]/float(value[0])
            market_price_list.append([key, avg])
        market_price_list.sort(key=lambda x: x[0])
        ma_short = [x[1] for x in build_exponential_moving_average(market_price_list, 12)]
        ma_long = [x[1] for x in build_exponential_moving_average(market_price_list, 26)]
        signal_line_p = [s - l for s, l in zip(ma_short, ma_long)]
        signal_line = [[market_price_list[i][0], signal_line_p[i]] for i in range(len(market_price_list))]
        ma_signal = build_exponential_moving_average(signal_line, 9)
        total_price_MACD = ma_signal
    return total_price_MACD


def get_total_market_price_MACD_dict():
    ma_signal = get_total_market_price_MACD()
    total_dict = {}
    for tupla in ma_signal:
        total_dict[tupla[0]] = tupla[1]
    return total_dict


def build_total_market_price_map():
    for set_dir in set_dirs:
        load_feature_selection_table(set_dir)
        prices_path = get_data_location() + "DATA\\MTGOprices\\Standard\\" + set_dir
        price_files = [f for f in listdir(prices_path) if isfile(join(prices_path, f))]
        for card_file in price_files:
            card_name = os.path.splitext(card_file)[0]
            """ consider only cards for which the feature selection table is defined"""
            if card_name in get_feature_selection_table(set_dir):
                timePriceList_raw = get_raw_prices(set_dir, card_file)
                last_day_seen = datetime.datetime.fromtimestamp(86400)
                for tupla in timePriceList_raw:
                    tupla[0] = datetime.datetime.fromtimestamp(tupla[0] / 1000.0)
                    key_string = tupla[0].strftime('%y%m%d')
                    """ remove duplicate days (24h sampling, to uniform with older data) and remove dates after simulation start (up_to_date)"""
                    if tupla[0].day != last_day_seen.day:
                        if key_string in total_market_price:
                            total_market_price[key_string][0] += 1
                            total_market_price[key_string][1] += tupla[1]
                        else:
                            total_market_price[key_string] = [1, tupla[1]]
                        last_day_seen = tupla[0]


def get_raw_prices(set_dir, card_file):
    with open(get_data_location() + "DATA\\MTGOprices\\Standard\\" + set_dir + "\\" + card_file) as datafile:
        rawjson = json.load(datafile)
    timePriceList_raw = rawjson["data"]
    if cut_start:
        timePriceList_raw = timePriceList_raw[cut_size:]
    return timePriceList_raw


def get_prices(set_dir, card_file):
    timePriceList_raw = get_raw_prices(set_dir, card_file)
    for tupla in timePriceList_raw:
        tupla[0] = datetime.datetime.fromtimestamp(tupla[0]/1000.0)
    return timePriceList_raw


def get_base_timeseries(set_dir, card_file, up_to_date = datetime.datetime.now(), normalized = True):

    standardizedTourCount = []
    standardizedBudgetCount = []
    limitedSupply = []
    standardExit = []
    standardizedAllGoldfishCount = []
    standardizedPtCount = []
    standardizedModernCount = []
    MACD_index = []
    RSI_index = []

    timePriceList_raw = get_raw_prices(set_dir, card_file)

    """uso derivata dei prezzi invece che i prezzi, derivata rispetto alla media degli ultimi deriv_avg_n valori"""
    if derivative:
        differentiate_timeseries(timePriceList_raw)

    """uniformo le date in millisec del dataset dei prezzi a oggetti py datetime"""
    closer_future_date_data = [datetime.datetime.now(), -1]
    timePriceList = []
    last_day_seen = datetime.datetime.fromtimestamp(86400)
    for tupla in timePriceList_raw:
        tupla[0] = datetime.datetime.fromtimestamp(tupla[0]/1000.0)
        """ remove duplicate days (24h sampling, to uniform with older data) and remove dates after simulation start (up_to_date)"""
        if tupla[0].day != last_day_seen.day:
            if tupla[0] < up_to_date:
                timePriceList.append(tupla)
                last_day_seen = tupla[0]
                if abs(tupla[0] - up_to_date) < abs(closer_future_date_data[0] - up_to_date) and tupla[0] - up_to_date > datetime.timedelta(0):
                    closer_future_date_data = tupla

    if len(timePriceList) > 0:

        """ creo uno starting point per i tornei 15 giorni prima del primo prezzo considerato """
        first_price_date = timePriceList[0][0]
        first_price_date -= datetime.timedelta(days=15)

        """ add price of next time instant wrt simulation start to build exogenous variables for prediciton """
        if closer_future_date_data[1] > -1 and len(timePriceList) > 0:
            timePriceList.append(closer_future_date_data)

        """ tourDateCount: dizionario --> data torneo = numero di quella carta in top8 """
        tourDateCount = build_tournament_history(os.path.splitext(card_file)[0], average, time, onlyMTGO, first_price_date)
        ptDateCount = build_pt_history(os.path.splitext(card_file)[0], first_price_date)

        checkmax_list = [x[1] for x in tourDateCount]
        """ valore di massimo dell'uso dei tornei, serve per creare soglia d'ingresso """
        max_val = max(checkmax_list)

        if len(tourDateCount) > 0 and max_val >= 1:
            """ costruisco standardizedTourCount, un dizionario in cui ad ogni giorno (date prese da quelle del dizionario dei prezzi,
            aggiornato giorno per giorno) associo l'uso di quella carta nel torneo più recente """
            for datePrice in timePriceList:
                biggerThanAny = True
                if datePrice[0] - tourDateCount[0][0] >= datetime.timedelta(days=1):
                    for budgetD in tourDateCount:
                        """ nelle liste ordinate il primo valore di data di torneo segnala che bisogna prendere in considerazione il torneo immediatamente precedente
                        Es. dateprice = 4 gennaio -> scorro la lista dei tornei fino al dateTour 5 gennaio che è > datePrice ->
                        considero il dateTour immediatamente precedente, ossia il primo dateTour < datePrice (es. 2 gennaio) """
                        if datePrice[0] < budgetD[0]:
                            tour_date_to_insert = budgetD[0]
                            index = tourDateCount.index(budgetD)
                            """ prendo l'esogeno del giorno precedente al prezzo per simulare l'assenza dell'esogeno del giorno nella realtà """
                            while tour_date_to_insert.day == datePrice[0].day or tour_date_to_insert >= datePrice[0]:
                                index -= 1
                                tour_date_to_insert = tourDateCount[index][0]
                                if index == 0: break
                            standardizedTourCount.append([datePrice[0], tourDateCount[index][1]])
                            biggerThanAny = False
                            break
                    """ se il prezzo ha una data posteriore a qualunque dato di torneo, replico l'ultimo dato e lo associo a questa data """
                    if biggerThanAny:
                        standardizedTourCount.append([datePrice[0], tourDateCount[-1][1]])
                else:
                    standardizedTourCount.append([datePrice[0], 0])

            """uso derivata ANCHE DEI TORNEI (vedi sopra sui prezzi per spiegazione)"""
            if derivative:
                differentiate_timeseries(standardizedTourCount)

            usedDays = set()
            for dateTour in standardizedTourCount:
                has_the_day = False
                for datePt in ptDateCount:
                    """ 3 because pt data file is set on Friday start but data is available only on Sunday (and then on Monday for prediction)"""
                    if (dateTour[0] - datePt[0]).days == 3:
                        day = dateTour[0].replace(hour=0, minute=0, second=0, microsecond=0)
                        if not day in usedDays:
                            has_the_day = True
                            standardizedPtCount.append([dateTour[0], datePt[1] - dateTour[1]])
                            usedDays.add(day)
                            break
                if not has_the_day:
                    standardizedPtCount.append([dateTour[0], 0])
            extend_timeseries_w_gamma(standardizedPtCount, 0.7)

            """costruisco la time_serie dell'uso di ogni carta nei Budget Decks di MTGoldfish"""
            budgetDateCount = build_budget_history(os.path.splitext(card_file)[0], average, time, first_price_date)
            for datePrice in timePriceList:
                biggerThanAny = True
                if datePrice[0] - budgetDateCount[0][0] >= datetime.timedelta(days=1):
                    for budgetD in budgetDateCount:
                        if datePrice[0] < budgetD[0]:
                            tour_date_to_insert = budgetD[0]
                            index = budgetDateCount.index(budgetD)
                            """ prendo l'esogeno del giorno precedente al prezzo per simulare l'assenza dell'esogeno del giorno nella realtà """
                            while tour_date_to_insert.day == datePrice[0].day or tour_date_to_insert >= datePrice[0]:
                                index -= 1
                                tour_date_to_insert = budgetDateCount[index][0]
                                if index == 0: break
                            standardizedBudgetCount.append([datePrice[0], budgetDateCount[index][1]])
                            biggerThanAny = False
                            break
                    if biggerThanAny:
                        standardizedBudgetCount.append([datePrice[0], budgetDateCount[-1][1]])
                else:
                    standardizedBudgetCount.append([datePrice[0], 0])


            """costruisco la time_serie dell'uso di ogni carta in tutte le altre rubriche di MTGoldfish"""
            AllGoldfishDateCount = build_all_goldfish_history(os.path.splitext(card_file)[0], average, time, first_price_date)
            for datePrice in timePriceList:
                biggerThanAny = True
                if datePrice[0] - AllGoldfishDateCount[0][0] >= datetime.timedelta(days=1):
                    for allGoldD in AllGoldfishDateCount:
                        if datePrice[0] < allGoldD[0]:
                            tour_date_to_insert = allGoldD[0]
                            index = AllGoldfishDateCount.index(allGoldD)
                            """ prendo l'esogeno del giorno precedente al prezzo per simulare l'assenza dell'esogeno del giorno nella realtà """
                            while tour_date_to_insert.day == datePrice[0].day or tour_date_to_insert >= datePrice[0]:
                                index -= 1
                                tour_date_to_insert = AllGoldfishDateCount[index][0]
                                if index == 0: break
                            standardizedAllGoldfishCount.append([datePrice[0], AllGoldfishDateCount[index][1]])
                            biggerThanAny = False
                            break
                    if biggerThanAny:
                        standardizedAllGoldfishCount.append([datePrice[0], AllGoldfishDateCount[-1][1]])
                else:
                    standardizedAllGoldfishCount.append([datePrice[0], 0])


            """costruisco la time_serie dell'uso di ogni carta nei tornei online Modern"""
            modernCount = build_modern_history(os.path.splitext(card_file)[0], average, time, first_price_date)
            for datePrice in timePriceList:
                biggerThanAny = True
                if datePrice[0] - modernCount[0][0] >= datetime.timedelta(days=1):
                    for modernD in modernCount:
                        if datePrice[0] < modernD[0]:
                            tour_date_to_insert = modernD[0]
                            index = modernCount.index(modernD)
                            """ prendo l'esogeno del giorno precedente al prezzo per simulare l'assenza dell'esogeno del giorno nella realtà """
                            while tour_date_to_insert.day == datePrice[0].day or tour_date_to_insert >= datePrice[0]:
                                index -= 1
                                tour_date_to_insert = modernCount[index][0]
                                if index == 0: break
                            standardizedModernCount.append([datePrice[0], modernCount[index][1]])
                            biggerThanAny = False
                            break
                    if biggerThanAny:
                        standardizedModernCount.append([datePrice[0], modernCount[-1][1]])
                else:
                    standardizedModernCount.append([datePrice[0], 0])

            #fill_supply_feature(set_dir, limitedSupply, timePriceList)
            #fill_standard_exit(set_dir, standardExit, timePriceList)

            MACD_index = build_MACD_index(timePriceList)
            RSI_index = build_RSI_index(timePriceList)

    time_series = [timePriceList, standardizedTourCount, standardizedBudgetCount, limitedSupply, standardExit,
                   standardizedAllGoldfishCount, standardizedPtCount, standardizedModernCount, MACD_index, RSI_index]

    if normalized:
        for serie in time_series:
            if serie:
                normalize_column(serie)
    return time_series



def build_RSI_index(timePriceList, periods=14):
    RSI_ts = []
    for index in range(len(timePriceList)):
        gains = []
        losses = []
        for i in range(periods):
            if index - (i+1) >= 0:
                delta = timePriceList[index - i][1] - timePriceList[index - i - 1][1]
                if delta > 0:
                    gains.append(delta)
                elif delta < 0:
                    losses.append(abs(delta))
        RSI = 0
        if len(gains) > 0 and len(losses) > 0:
            RSI_up = sum(gains)/float(len(gains))
            RSI_down = sum(losses)/float(len(losses))
            if RSI_down != 0:
                RSI = 100 - 100/(1 + RSI_up/RSI_down)
        RSI_ts.append([timePriceList[index][0],RSI])
    return RSI_ts



def build_MACD_index(timePriceList, short_period=12, long_period=26, signal_period=9):
    ma_short = [x[1] for x in build_exponential_moving_average(timePriceList, short_period)]
    ma_long = [x[1] for x in build_exponential_moving_average(timePriceList, long_period)]
    signal_line_p = [s - l for s, l in zip(ma_short, ma_long)]
    signal_line = [[timePriceList[i][0], signal_line_p[i]] for i in range(len(timePriceList))]
    ma_signal = build_exponential_moving_average(signal_line, signal_period)
    return ma_signal


def build_exponential_moving_average(prices, periods):
    ma_prices = []
    for index in range(len(prices)):
        weight = 0
        elem = []
        for i in range(periods):
            if index - i >= 0:
                coeff = 2/float(i+2)
                elem.append(coeff*prices[index - i][1])
                weight = weight + coeff
        res = (sum(elem) / float(weight))
        ma_prices.append([prices[index][0], res])
    return ma_prices



def normalize_column(list_of_lists):
    column = [x[1] for x in list_of_lists]
    minval = min(column)
    maxval = max(column)
    if maxval - minval != 0:
        for tuple in list_of_lists:
            tuple[1] = (tuple[1] - minval) / (maxval - minval)
    return list_of_lists


def normalize_list(list):
    list_copy = copy.deepcopy(list)
    minval = min(list)
    maxval = max(list)
    if maxval - minval != 0:
        list = [(i - minval) / (maxval - minval) for i in list_copy]
    return list



def fill_supply_feature(set_dir, limitedSupply, timePriceList):
    if set_dir == "AER":
        for datePrice in timePriceList:
            if datePrice[0] < datetime.datetime.fromtimestamp(releases["AER"]/1000.0):
                limitedSupply.append([datePrice[0], 0])
            else:
                limitedSupply.append([datePrice[0], 2 * 100 / float(card_count[set_dir])])
    elif set_dir == "KLD":
        for datePrice in timePriceList:
            if datePrice[0] < datetime.datetime.fromtimestamp(releases["KLD"]/1000.0):
                limitedSupply.append([datePrice[0], 0])
            elif datePrice[0] < datetime.datetime.fromtimestamp(releases["AER"]/1000.0):
                limitedSupply.append([datePrice[0], 3 * 100 / float(card_count[set_dir])])
            else:
                limitedSupply.append([datePrice[0], 1 * 100 / float(card_count[set_dir])])
    elif set_dir == "EMN":
        for datePrice in timePriceList:
            if datePrice[0] < datetime.datetime.fromtimestamp(releases["EMN"]/1000.0):
                limitedSupply.append([datePrice[0], 0])
            elif datePrice[0] < datetime.datetime.fromtimestamp(releases["KLD"]/1000.0):
                limitedSupply.append([datePrice[0], 2 * 100 / float(card_count[set_dir])])
            else:
                limitedSupply.append([datePrice[0], 0])
    elif set_dir == "SOI":
        for datePrice in timePriceList:
            if datePrice[0] < datetime.datetime.fromtimestamp(releases["SOI"]/1000.0):
                limitedSupply.append([datePrice[0], 0])
            elif datePrice[0] < datetime.datetime.fromtimestamp(releases["EMN"]/1000.0):
                limitedSupply.append([datePrice[0], 3 * 100 / float(card_count[set_dir])])
            elif datePrice[0] < datetime.datetime.fromtimestamp(releases["KLD"]/1000.0):
                limitedSupply.append([datePrice[0], 1 * 100 / float(card_count[set_dir])])
            else:
                limitedSupply.append([datePrice[0], 0])
    elif set_dir == "OGW":
        for datePrice in timePriceList:
            if datePrice[0] < datetime.datetime.fromtimestamp(releases["OGW"]/1000.0):
                limitedSupply.append([datePrice[0], 0])
            elif datePrice[0] < datetime.datetime.fromtimestamp(releases["SOI"]/1000.0):
                limitedSupply.append([datePrice[0], 2 * 100 / float(card_count[set_dir])])
            else:
                limitedSupply.append([datePrice[0], 0])
    elif set_dir == "BFZ":
        for datePrice in timePriceList:
            if datePrice[0] < datetime.datetime.fromtimestamp(releases["BFZ"]/1000.0):
                limitedSupply.append([datePrice[0], 0])
            elif datePrice[0] < datetime.datetime.fromtimestamp(releases["OGW"]/1000.0):
                limitedSupply.append([datePrice[0], 3 * 100 / float(card_count[set_dir])])
            elif datePrice[0] < datetime.datetime.fromtimestamp(releases["SOI"]/1000.0):
                limitedSupply.append([datePrice[0], 1 * 100 / float(card_count[set_dir])])
            else:
                limitedSupply.append([datePrice[0], 0])


def fill_standard_exit(set_dir, standardExit, timePriceList):
    if set_dir == "DTK":
        for datePrice in timePriceList:
            delta = datetime.datetime.fromtimestamp(standard_exit["DTK"]/1000.0) - datePrice[0]
            margin = 90 - delta.days
            if margin > 90:
                margin = 90
            if margin > 0:
                standardExit.append([datePrice[0], margin])
            else:
                standardExit.append([datePrice[0], 0])


def differentiate_timeseries(time_serie):
    copy_list = copy.deepcopy(time_serie)
    for i in range(len(time_serie)):
        counted = 0
        avg = 0
        for j in range(1, deriv_avg_n):
            if i - j > 0:
                avg += copy_list[i - j][1]
                counted += 1
        if counted > 0:
            avg = avg / counted
        else:
            avg = copy_list[0][1]
        delta = copy_list[i][1] - avg
        time_serie[i][1] = delta


if __name__ == "__main__":
    get_total_market_price_MACD()