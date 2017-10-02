# coding=utf-8
from TournamentReader import *
from GraphMaker import *
import os
import copy


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
standard_exit = {"DTK": 1476050400000}


def get_base_timeseries(set_dir, card_file, normalized):

    with open("C:\\Users\\pitu\\Desktop\\DATA\\MTGOprices\\Standard\\" + set_dir + "\\" + card_file) as datafile:
        rawjson = json.load(datafile)
    timePriceList = rawjson["data"]

    """remove prices of the first 15 days due to the high frequency"""
    if cut_start:
        timePriceList = timePriceList[cut_size:]

    """uso derivata dei prezzi invece che i prezzi, derivata rispetto alla media degli ultimi deriv_avg_n valori"""
    if derivative:
        copy_list = copy.deepcopy(timePriceList)
        for i in xrange(len(timePriceList)):
            counted = 0
            avg = 0
            for j in xrange (1, deriv_avg_n):
                if (i -  j > 0):
                    avg += copy_list[i - j][1]
                    counted += 1
            if counted > 0:
                avg = avg / counted
            else:
                avg = copy_list[0][1]
            delta = copy_list[i][1] - avg
            timePriceList[i][1] = delta


    """uniformo le date in millisec del dataset dei prezzi a oggetti py datetime"""
    for tupla in timePriceList:
        tupla[0] = datetime.datetime.fromtimestamp(tupla[0]/1000.0)

    """ tourDateCount: dizionario --> data torneo = numero di quella carta in top8 """
    tourDateCount = build_tournament_history(os.path.splitext(card_file)[0], average, time, onlyMTGO)

    checkmax_list = [x[1] for x in tourDateCount]
    """ valore di massimo dell'uso dei tornei, serve per creare soglia d'ingresso """
    max_val = max(checkmax_list)

    standardizedTourCount = []
    standardizedBudgetCount = []
    limitedSupply = []
    standardExit = []

    if len(tourDateCount) > 0 and max_val >= 1:
        """ costruisco standardizedTourCount, un dizionario in cui ad ogni giorno (date prese da quelle del dizionario dei prezzi,
        aggiornato giorno per giorno) associo l'uso di quella carta nel torneo più recente """
        for datePrice in timePriceList:
            biggerThanAny = True
            for budgetD in tourDateCount:
                """ nelle liste ordinate il primo valore di data di torneo segnala che bisogna prendere in considerazione il torneo immediatamente precedente
                Es. dateprice = 4 gennaio -> scorro la lista dei tornei fino al dateTour 5 gennaio che è > datePrice ->
                considero il dateTour immediatamente precedente, ossia il primo dateTour < datePrice (es. 2 gennaio) """
                if datePrice[0] < budgetD[0]:
                    standardizedTourCount.append([datePrice[0], previous[1]])
                    biggerThanAny = False
                    break
                previous = budgetD
            """ se il prezzo ha una data posteriore a qualunque dato di torneo, replico l'ultimo dato e lo associo a questa data """
            if biggerThanAny:
                standardizedTourCount.append([datePrice[0], tourDateCount[-1][1]])

        """uso derivata ANCHE DEI TORNEI (vedi sopra sui prezzi per spiegazione)"""
        if derivative:
            copy_list = copy.deepcopy(standardizedTourCount)
            for i in xrange(len(standardizedTourCount)):
                counted = 0
                avg = 0
                for j in xrange(1, deriv_avg_n):
                    if (i - j > 0):
                        avg += copy_list[i - j][1]
                        counted += 1
                if counted > 0:
                    avg = avg / counted
                else:
                    avg = copy_list[0][1]
                delta = copy_list[i][1] - avg
                standardizedTourCount[i][1] = delta

        """ tourDateCount: dizionario --> data torneo = numero di quella carta in top8 """
        budgetDateCount = build_budget_history(os.path.splitext(card_file)[0], average, time)

        for datePrice in timePriceList:
            biggerThanAny = True
            for budgetD in budgetDateCount:
                if datePrice[0] < budgetD[0]:
                    standardizedBudgetCount.append([datePrice[0], previous[1]])
                    biggerThanAny = False
                    break
                previous = budgetD
            if biggerThanAny:
                standardizedBudgetCount.append([datePrice[0], budgetDateCount[-1][1]])

        #fill_supply_feature(set_dir, limitedSupply, timePriceList)
        fill_standard_exit(set_dir, standardExit, timePriceList)

        if normalized:
            normalize_column(timePriceList)
            normalize_column(standardizedTourCount)
            normalize_column(standardizedBudgetCount)
            #normalize_column(limitedSupply)
            normalize_column(standardExit)

    return [timePriceList, standardizedTourCount, standardizedBudgetCount, limitedSupply, standardExit]



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


def get_file_name(AR, MA):
    return  "AR" + str(AR) + "_MA" + str(MA)+ "_BUDGET_PACKS"



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
    pprint(standardExit)
