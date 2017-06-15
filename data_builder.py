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


def get_base_timeseries(set_dir, card_file):

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
    if len(tourDateCount) > 0 and max_val >= 1:
        """ costruisco standardizedTourCount, un dizionario in cui ad ogni giorno (date prese da quelle del dizionario dei prezzi,
        aggiornato giorno per giorno) associo l'uso di quella carta nel torneo più recente """
        for datePrice in timePriceList:
            biggerThanAny = True
            for dateTour in tourDateCount:
                """ nelle liste ordinate il primo valore di data di torneo segnala che bisogna prendere in considerazione il torneo immediatamente precedente
                Es. dateprice = 4 gennaio -> scorro la lista dei tornei fino al dateTour 5 gennaio che è > datePrice ->
                considero il dateTour immediatamente precedente, ossia il primo dateTour < datePrice (es. 2 gennaio) """
                if datePrice[0] < dateTour[0]:
                    standardizedTourCount.append([datePrice[0], previous[1]])
                    biggerThanAny = False
                    break
                previous = dateTour
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

    return [timePriceList, standardizedTourCount]