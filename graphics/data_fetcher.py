from data_parsing.data_builder import *
import re
import scipy.stats as st


standard_sim_2 = ['2016_04_01', '2016_06_01', '2016_08_01', '2016_10_01', '2016_12_01', '2017_02_01']
standard_sim_3 = ['2016_04_01', '2016_07_01', '2016_10_01', '2017_01_01']
types_to_names = {"0_0.txt": "SL/TP = 0", "0.0_0.0.txt": "SL/TP = 0", "0.2_0.2.txt": "SL/TP = 0.2",
                  "0.4_0.4.txt": "SL/TP = 0.4", "0.6_0.6.txt": "SL/TP = 0.6",
                  "0.8_0.8.txt": "SL/TP = 0.8"}
windows_to_names = {"SL_ALL" : "POL", "SL_RND" : "RND"}


def transform_simulations_in_boxplot():
    types = ["0_0.txt", "0.2_0.2.txt", "0.4_0.4.txt", "0.6_0.6.txt", "0.8_0.8.txt"]

    object = "SL120_Simulations\\B2000\\2 months"
    base_files_path = get_data_location() + object
    subfolders = next(os.walk(base_files_path))[1]
    pprint(subfolders)

    for th_type in types:
        final_results = []
        xes = []
        names = []
        lists = []
        for subfolder in subfolders:
            if subfolder in standard_sim_2:
                files_path = join(base_files_path, subfolder)
                validation_files = [f for f in listdir(files_path) if isfile(join(files_path, f))]
                for validation_file_name in validation_files:
                    if th_type in validation_file_name:
                        f = open(join(files_path, validation_file_name), "r")
                        value = False
                        for line in f:
                            if "BUDGET FINALE" in line:
                                value = True
                            elif value:
                                final_results.append(float(re.findall(r"[-+]?\d*\.\d+|\d+", line)[0]))
                                value = False
                        f.close()
                xes.append(subfolder.replace("_", "/"))
                names.append(subfolder.replace("_", "/"))
                lists.append(final_results)
                final_results = []
        draw_box_graph(names, xes, lists, object.replace("\\", "_") + "_" + th_type, False)


def transform_simulations_in_grouped_boxplot():
    budgets = [500, 1000, 2000, 5000]
    windows = ["SL60", "SL90", "SL120", "SL_ALL"]
    months = ["2 months", "3 months"]
    types = ["0_0.txt", "0.2_0.2.txt", "0.4_0.4.txt", "0.6_0.6.txt", "0.8_0.8.txt"]

    for month in months:
        for window in windows:
            for budget in budgets:
                object = window + "_Simulations\\B" + str(budget) + "\\" + month
                base_files_path = get_data_location() + object
                subfolders = next(os.walk(base_files_path))[1]
                pprint(subfolders)

                xes = []
                names = []
                lists = []
                for th_type in types:
                    final_results = []
                    temp_x = []
                    for subfolder in subfolders:
                        if month == "2 months":
                            date_set = standard_sim_2
                        else:
                            date_set = standard_sim_3
                        if subfolder in date_set:
                            files_path = join(base_files_path, subfolder)
                            validation_files = [f for f in listdir(files_path) if isfile(join(files_path, f))]
                            for validation_file_name in validation_files:
                                if th_type in validation_file_name:
                                    f = open(join(files_path, validation_file_name), "r")
                                    value = False
                                    for line in f:
                                        if "BUDGET FINALE" in line:
                                            value = True
                                        elif value:
                                            res = float(re.findall(r"[-+]?\d*\.\d+|\d+", line)[0])
                                            margin = res - budget
                                            percentage = margin / float(budget) * 100
                                            final_results.append(percentage)
                                            temp_x.append(subfolder.replace("_", "/"))
                                            value = False
                                    f.close()
                    names.append(types_to_names[th_type])
                    lists.append(final_results)
                    xes.append(temp_x)
                draw_box_graph(names, xes, lists, object.replace("\\", "_"), True, 0)


def transform_in_benchmark_grouped_boxplot():
    budgets = [1000]
    windows = ["SL_ALL", "SL_RND"]
    months = ["3 months"]
    types = ["0.6_0.6.txt"]

    for month in months:
        for budget in budgets:
            xes = []
            names = []
            lists = []
            for window in windows:
                object = window + "_Simulations\\B" + str(budget) + "\\" + month
                base_files_path = get_data_location() + object
                subfolders = next(os.walk(base_files_path))[1]
                pprint(subfolders)

                for th_type in types:
                    final_results = []
                    temp_x = []
                    for subfolder in subfolders:
                        if month == "2 months":
                            date_set = standard_sim_2
                        else:
                            date_set = standard_sim_3
                        if subfolder in date_set:
                            files_path = join(base_files_path, subfolder)
                            validation_files = [f for f in listdir(files_path) if isfile(join(files_path, f))]
                            for validation_file_name in validation_files:
                                if th_type in validation_file_name:
                                    f = open(join(files_path, validation_file_name), "r")
                                    value = False
                                    for line in f:
                                        if "BUDGET FINALE" in line:
                                            value = True
                                        elif value:
                                            res = float(re.findall(r"[-+]?\d*\.\d+|\d+", line)[0])
                                            margin = res - budget
                                            percentage = margin / float(budget) * 100
                                            final_results.append(percentage)
                                            temp_x.append(subfolder.replace("_", "/"))
                                            value = False
                                    f.close()
                    names.append(windows_to_names[window])
                    lists.append(final_results)
                    xes.append(temp_x)
            draw_box_graph(names, xes, lists, object.replace("\\", "_"), True, 0)


def make_real_mean_intervals_graph():
    types = ["0.6_0.6.txt"]
    budget = "1000"
    months = "3 months"

    objects = ["SL_ALL_Simulations\\B" + budget + "\\" + months, "SL_RND_Simulations\\B" + budget + "\\" + months]

    triplets = []
    xes = []
    names = []
    for sim_object in objects:
        base_files_path = get_data_location() + sim_object
        pprint(base_files_path)
        subfolders = next(os.walk(base_files_path))[1]
        pprint(subfolders)
        for th_type in types:
            if "RND" in sim_object:
                name = "RND " + types_to_names[th_type]
            else:
                name = types_to_names[th_type]
            names.append(name)
            triplet = [[], [], []]
            final_results = []
            first_it = True
            for subfolder in subfolders:
                if subfolder in standard_sim_3:
                    files_path = join(base_files_path, subfolder)
                    validation_files = [f for f in listdir(files_path) if isfile(join(files_path, f))]
                    for validation_file_name in validation_files:
                        if th_type in validation_file_name:
                            f = open(join(files_path, validation_file_name), "r")
                            value = False
                            for line in f:
                                if "BUDGET FINALE" in line:
                                    value = True
                                elif value:
                                    res = float(re.findall(r"[-+]?\d*\.\d+|\d+", line)[0])
                                    margin = res - int(budget)
                                    percentage = margin / float(budget) * 100
                                    final_results.append(percentage)
                                    value = False
                            f.close()
                    if first_it:
                        xes.append(subfolder.replace("_", "/"))
                    triplet[1].append(np.mean(final_results))
                    ints = get_confidence_interval(final_results)
                    triplet[0].append(ints[0])
                    triplet[2].append(ints[1])
                    final_results = []
            triplets.append(triplet)
    make_intervals_comparison_graph(xes, names, triplets, sim_object.replace("\\", "_") + "_" + th_type, 0)



def make_running_profit_graph():

    object = "Running_Profit"
    base_files_path = get_data_location() + object
    budget = 1000

    validation_files = [f for f in listdir(base_files_path) if isfile(join(base_files_path, f))]
    names = []
    dates = []
    profits = []
    first_it = True
    for validation_file_name in validation_files:
        f = open(join(base_files_path, validation_file_name), "r")
        names.append(validation_file_name.replace(".txt", ""))
        running_profit = []
        for line in f:
            if "**********" in line:
                trimmed = line.replace("*", "").strip()
                date = datetime.datetime.strptime(trimmed, "%Y-%m-%d %H:%M:%S")
                if first_it:
                    dates.append(date)
            if "PATRIMONIO CORRENTE" in line:
                res = float(re.findall(r"[-+]?\d*\.\d+|\d+", line)[0])
                pprint(res)
                margin = res - int(budget)
                percentage = margin / float(budget) * 100
                running_profit.append(percentage)
        profits.append(running_profit)
        f.close()
        first_it = False
    pprint(profits)
    draw_running_profit_graph(dates, names, profits, "Running_Profit", budget)


def get_confidence_interval(a):
    return st.t.interval(0.95, len(a) - 1, loc=np.mean(a), scale=st.sem(a))



if __name__ == "__main__":
    # transform_in_benchmark_grouped_boxplot()
    # transform_simulations_in_grouped_boxplot()
    # transform_simulations_in_boxplot()
    make_real_mean_intervals_graph()
    # make_running_profit_graph()