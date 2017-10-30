# coding=utf-8
from data_builder import *
from os import listdir
from os.path import isfile, join
import os
import pandas as pd
import pyflux as pf
import numpy as np
import math


""" TODO:
 - risolvere la mancanza di tornei per i periodi carenti del 2015 (DTK) costruendo un crawler direttamente per il sito wizard 
 (su mTGtop8 sono presenti solo uno o due mazzi per quesi tornei)
 - provare a usare termini di lag usage a intervalli più ampii nella regression (t-5, t-10...)
"""


#set_dirs = ["DTK", "AER", "KLD", "SOI", "EMN", "BFZ", "OGW"]
""" directory dei set dai quali prendere i dati dei prezzi, cambiare la lista per considerare diversi set al lancio """
set_dirs = ["TST"];


""" numero di lags autoregressivi presi in considerazione """
AR = 1
""" numero di moving averages prese in considerazione """
MA = 3
""" numero di steps in avanti della predizione """
steps = 1

""" fitting in sample o unico a inizio predizione"""
fit_always = False


base_path = get_data_location() + "PREDICTIONS\\"
MSEs = {}

""" dictionary that stores the trained model for each card indexed by card name """
models_table = {}


def get_file_name(AR, MA):
    return "NOREFIT_AR" + str(AR) + "_MA" + str(MA)+ "_FEATURE_SELECTION_W_INDEXS"


def sequential_forward_feature_selection(df, prices):
    features_raw = df.columns.values.tolist()
    features_raw.remove('prices')

    to_remove = []
    for feat in features_raw:
        if not df[feat].max() > 0:
            to_remove.append(feat)
    features = [x for x in features_raw if x not in to_remove]

    minSSE = 0
    formula = 'prices ~ 1'
    improving = True

    """only autoregressive model evaluation"""
    model = pf.ARIMAX(data=df, formula=formula, ar=AR, ma=MA)
    model.fit("MLE")
    n_prediction_samples = len(prices) / 4
    predicted_df = model.predict_is(n_prediction_samples, not fit_always, "MLE")
    real_prices = df['prices'].values.tolist()[- n_prediction_samples:]
    predicted_prices = predicted_df['prices'].values.tolist()
    for real, pred in zip(real_prices, predicted_prices):
        minSSE += (real - pred) ** 2

    while improving:
        improving = False
        for feat in features:
            formula_try = formula + " + " + feat
            model = pf.ARIMAX(data=df, formula=formula_try, ar=AR, ma=MA)
            model.fit("MLE")
            n_prediction_samples = len(prices) / 4
            predicted_df = model.predict_is(n_prediction_samples, not fit_always, "MLE")
            real_prices = df['prices'].values.tolist()[- n_prediction_samples:]
            predicted_prices = predicted_df['prices'].values.tolist()
            SSE = 0
            for real, pred in zip(real_prices, predicted_prices):
                SSE += (real - pred) ** 2
            pprint("SSE precedente: " + str(minSSE))
            pprint("SSE Modello con formula " + str(formula_try) + ": " + str(SSE))

            if SSE < minSSE:
                minSSE = SSE
                pprint("Procedo con feature successiva, includendo " + feat)
                formula = formula_try
                features.remove(feat)
                improving = True
                break

        if not improving:
            pprint("Nessun miglioramento, interrompo procedura")

    return formula


def get_ARIMAX_prediction(set_dir, card_file, datafile, write_data, make_graph, up_to_date, simulation_mode):

    normalized = True
    if simulation_mode:
        normalized = False
    time_series = get_base_timeseries(set_dir, card_file, up_to_date, normalized)

    timePriceList = time_series[0]
    standardizedTourCount = time_series[1]
    budgetCount = time_series[2]
    limitedSupply = time_series[3]  # non usato
    standardExit = time_series[4]  # non usato
    allGoldfishCount = time_series[5]
    ptExpectation = time_series[6]
    modernTourCount = time_series[7]
    MACD_index = time_series[8]
    RSI_index = time_series[9]

    if len(standardizedTourCount) > 0 and len(timePriceList) > 0:
        tours = [x[1] for x in standardizedTourCount]
        max_val = max(tours)
        if max_val > 0:
            dates = [x[0] for x in timePriceList]
            prices = [x[1] for x in timePriceList]
            budget = [x[1] for x in budgetCount]
            packs = [x[1] for x in limitedSupply]
            exits = [x[1] for x in standardExit]
            allGoldfish = [x[1] for x in allGoldfishCount]
            ptExps = [x[1] for x in ptExpectation]
            modern = [x[1] for x in modernTourCount]
            MACD = [x[1] for x in MACD_index]
            RSI = [x[1] for x in RSI_index]

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
            data = {"dates": dates, "prices": prices, "usage": tours,
                    "budget": budget, "allG": allGoldfish, "ptExps": ptExps, "modern": modern, "MACD": MACD,
                    "RSI": RSI}  # "packs":packs "trend":trend, "exit":exits, "usage1":tours1, "usage2":tours2, "usage3":tours3, "usage4":tours4

            """ CHANGE THIS LINE TO CHANGE THE DATAFRAME USED IN PREDICTION """
            df = pd.DataFrame(data, columns=['dates', 'prices', 'usage', 'budget', 'allG', 'ptExps', 'modern', 'MACD',
                                             'RSI'])  # 'packs', 'exit', usage1', 'usage2', 'usage3', 'usage4'])#, 'trend'])
            df.index = df['dates']
            del df['dates']

            """ creazione modello ARIMAX ## CHANGE THE FORMULA FOR DIFFERENT PREDICTIONS """
            if max(budget) > 0:
                formula = 'prices ~ 1 + usage + budget + MACD'
            else:
                formula = 'prices ~ 1 + usage + MACD'

            #formula = sequential_forward_feature_selection(df, prices)
            #formula = 'prices ~ 1 + usage + budget + ptExps'

            model = pf.ARIMAX(data=df, formula=formula, ar=AR, ma=MA)
            """ if we are in simulation mode we stored the card's model latent variables to reuse at each time step """
            if simulation_mode and card_file in models_table:
                model.latent_variables = models_table[card_file]
            else:
                x = model.fit("MLE")
                saved_lvs = model.latent_variables
                if simulation_mode:
                    models_table[card_file] = model.latent_variables

            title = os.path.splitext(card_file)[0]

            if write_data:
                """ print to file analysis of created model"""
                datafile.write("\n\n")
                datafile.write(title)
                datafile.write("\n")
                for s in x.summary():
                    datafile.write(str(s))

            if simulation_mode:
                n_prediction_samples = 1
            else:
                n_prediction_samples = len(prices) / 4

            if steps > 1 and not simulation_mode:
                """ predizione a steps dell'ultimo quarto di timeseries"""

                to_predict = n_prediction_samples
                first_it = True
                while to_predict > steps:
                    data1 = df.iloc[:-to_predict, :]
                    data2 = df.iloc[-to_predict:, :]
                    if fit_always:
                        model = pf.ARIMAX(data=data1, formula=formula, ar=AR, ma=MA)
                        model.fit("MLE")
                    else:
                        model = pf.ARIMAX(data=data1, formula=formula, ar=AR, ma=MA)
                        model.latent_variables = saved_lvs
                    if first_it:
                        predicted_df = model.predict(steps, oos_data=data2, intervals=False)
                        first_it = False
                    else:
                        predicted_df = pd.concat(
                            [predicted_df, model.predict(h=steps, oos_data=data2, intervals=False)])
                    to_predict = to_predict - steps

            else:
                """ predizione rolling-in sample dell'ultimo quarto di timeseries"""
                predicted_df = model.predict_is(n_prediction_samples, not fit_always, "MLE")

            prices = df['prices'].values.tolist()[- n_prediction_samples:]
            predicted_prices = predicted_df['prices'].values.tolist()

            SSE = 0
            for real, pred in zip(prices, predicted_prices):
                SSE += (real - pred) ** 2
            MSE = SSE / len(predicted_prices)
            MSEs[title] = MSE

            if write_data:
                datafile.write("MSE: ")
                datafile.write(str(MSE) + "\n")

            if make_graph:
                """ manda a plotly per disegnare grafico dell'ultimo quarto di timeseries real/predicted"""
                make_prediction_graph(dates[- n_prediction_samples:], prices, predicted_prices, title,
                                      join(set_dir, get_file_name(AR, MA)), MSE)

            return [df, predicted_df]
    return None




for set_dir in set_dirs:

    if not os.path.exists(set_dir):
        os.makedirs(set_dir)
    prices_path = get_data_location() + "DATA\\MTGOprices\\Standard\\" + set_dir

    price_files = [f for f in listdir(prices_path) if isfile(join(prices_path, f))]

    averages_residuals = []
    variances_residuals = []

    with open(get_data_location() + "PREDICTIONS\\" + set_dir + "\\" + "_prediction_analysis_" + get_file_name(AR, MA) + ".txt", "w") as datafile:
        if not os.path.exists(join(base_path, join(set_dir, get_file_name(AR, MA) ))):
            os.makedirs(join(base_path, join(set_dir, get_file_name(AR, MA) )))
        for card_file in price_files:

                    df_list = get_ARIMAX_prediction(set_dir, card_file, datafile, True, True, datetime.datetime.now(), False)
                    if df_list is not None:
                        df = df_list[0]
                        predicted_df = df_list[1]
                        predicted_prices = predicted_df['prices'].values.tolist()
                        prices = df['prices'].values.tolist()[- len(predicted_prices):]
                        title = os.path.splitext(card_file)[0]

                        """analisi residui"""
                        delta_pred = [real - pred for real, pred in zip(prices, predicted_prices)]
                        avg_residuals = sum(delta_pred)/float(len(delta_pred))
                        averages_residuals.append(avg_residuals)
                        var_residuals = np.var(delta_pred)
                        variances_residuals.append(var_residuals)
                        datafile.write("Average Residuals: ")
                        datafile.write(str(avg_residuals) + "\n")
                        datafile.write("Variance Residuals: ")
                        datafile.write(str(var_residuals) + "\n")

        if len(MSEs) > 0:
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
        if len(averages_residuals) > 0 and len(variances_residuals) > 0:
            total_avgs = sum(averages_residuals)
            datafile.write("Sum of Residuals Averages of set " + set_dir + "\n")
            datafile.write(str(total_avgs) + "\n")
            mean_avgs = total_avgs/float(len(averages_residuals))
            datafile.write("Average of Residuals Averages of set " + set_dir + "\n")
            datafile.write(str(mean_avgs) + "\n")
            total_vars = sum(variances_residuals)
            datafile.write("Sum of Residuals Variances of set " + set_dir + "\n")
            datafile.write(str(total_vars) + "\n")
            mean_vars = total_vars / float(len(variances_residuals))
            datafile.write("Average of Residuals Variances of set " + set_dir + "\n")
            datafile.write(str(mean_vars) + "\n")







