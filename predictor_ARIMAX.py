# coding=utf-8
from data_builder import *
from os import listdir
from os.path import isfile, join
import os
import pandas as pd
import pyflux as pf
import math


""" TODO:
 - risolvere la mancanza di tornei per i periodi carenti del 2015 (DTK) costruendo un crawler direttamente per il sito wizard 
 (su mTGtop8 sono presenti solo uno o due mazzi per quesi tornei)
 - normalizzare le timeseries con y tra 0 e 1 per avere paragoni dei coefficienti beta consistenti tra loro
 - provare a usare termini di lag usage a intervalli più ampii nella regression (t-5, t-10...)
 - pensare a ulteriori features come uscita standard e questione domanda/offerta bustine limited
"""


#set_dirs = ["DTK", "AER", "KLD", "SOI", "EMN", "BFZ", "OGW"]
""" directory dei set dai quali prendere i dati dei prezzi, cambiare la lista per considerare diversi set al lancio """
set_dirs = ["KLDH"]

""" numero di lags autoregressivi presi in considerazione """
AR = 3
""" numero di moving averages prese in considerazione """
MA = 3
MSEs = {}

base_path = "C:\\Users\\pitu\\Desktop\\PREDICTIONS\\"


for set_dir in set_dirs:

    if not os.path.exists(set_dir):
        os.makedirs(set_dir)
    prices_path = "C:\\Users\\pitu\\Desktop\\DATA\\MTGOprices\\Standard\\" + set_dir

    price_files = [f for f in listdir(prices_path) if isfile(join(prices_path, f))]
    with open("C:\\Users\\pitu\\Desktop\\PREDICTIONS\\" + set_dir + "\\"
                      + "_prediction_analysis_AR " + str(AR) + "_MA" + str(MA) + ".txt", "w") as datafile:
        for card_file in price_files:

            time_series = get_base_timeseries(set_dir, card_file)
            timePriceList = time_series[0]
            standardizedTourCount = time_series[1]
            if (len(standardizedTourCount) > 0):

                dates = [x[0] for x in timePriceList]
                prices = [x[1] for x in timePriceList]
                tours = [x[1] for x in standardizedTourCount]

                """ negative trend feature (slowly decreasing exponential) """
                trend = []
                for i in xrange(len(prices)):
                    trend.append(math.exp( -(i+365)/float(365) ))

                """ create lagged usage timeseries """
                tours1 = copy.deepcopy(tours)
                del tours1[0]
                tours1.append(tours1[-1])
                tours2 = copy.deepcopy(tours1)
                del tours2[0]
                tours2.append(tours2[-1])
                tours3 = copy.deepcopy(tours2)
                del tours3[0]
                tours3.append(tours3[-1])
                tours4 = copy.deepcopy(tours3)
                del tours4[0]
                tours4.append(tours4[-1])

                """ pandas DataFrame creation with our timeseries"""
                data = {"dates":dates, "prices": prices, "usage":tours, "usage1":tours1, "usage2":tours2, "usage3":tours3, "usage4":tours4, "trend":trend}

                """ CHANGE THIS LINE TO CHANGE THE DATAFRAME USED IN PREDICTION """
                df = pd.DataFrame(data, columns=['dates', 'prices', 'usage'])# 'usage1', 'usage2', 'usage3', 'usage4'])#, 'trend'])
                df.index = df['dates']
                del df['dates']

                """ creazione modello ARIMAX ## CHANGE THE FORMULA FOR DIFFERENT PREDICTIONS """
                model = pf.ARIMAX(data=df, formula='prices ~ 1 + usage' , ar=AR, ma=MA)
                x = model.fit("MLE")

                title = os.path.splitext(card_file)[0]

                """ print to file analysis of created model"""
                datafile.write("\n\n")
                datafile.write(title)
                datafile.write("\n")
                for s in x.summary():
                    datafile.write(str(s))

                """ predizione rolling-in sample dell'ultimo quarto di timeseries"""
                n_prediction_samples = len(prices) / 4
                predicted_df = model.predict_is(n_prediction_samples, False, "MLE")

                """ manda a plotly per disegnare grafico dell'ultimo quarto di timeseries real/predicted"""
                prices = df['prices'].values.tolist()[- n_prediction_samples:]
                predicted_prices = predicted_df['prices'].values.tolist()

                SSE = 0
                for real, pred in zip(prices, predicted_prices):
                    increment = (real - pred)**2
                    SSE += (real - pred)**2
                MSE = SSE/n_prediction_samples
                MSEs[title] = MSE
                datafile.write("MSE: ")
                datafile.write(str(MSE) + "\n")

                make_prediction_graph(dates[- n_prediction_samples:], prices, predicted_prices, title, set_dir, MSE)

        totalMSE = 0
        meanMSE = 0
        for MSE in MSEs.values():
            totalMSE += MSE
        meanMSE = totalMSE/len(MSEs)

        datafile.write("\n\n")
        datafile.write("ARIMAX model with AR " + str(AR) + " and MA " + str(MA) + "\n")
        datafile.write("Total MSE of set " + set_dir + "\n")
        datafile.write(str(totalMSE) + "\n")
        datafile.write("Mean MSE of set " + set_dir + "\n")
        datafile.write(str(meanMSE)+ "\n")







