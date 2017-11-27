import json
import os
import shutil
from os import listdir
from os.path import isfile, join

from data_parsing.data_builder import get_data_location
from data_parsing.tournament_reader import get_tournament_date

base_path = get_data_location() + "\New"
useless_path = "not_significant"
if not os.path.exists(join(base_path, useless_path)):
    os.makedirs(join(base_path, useless_path))


tour_files = [f for f in listdir(base_path) if isfile(join(base_path, f))]

for f in tour_files:
    t_file = join(base_path, f)
    with open(t_file) as datafile:
        raw_tour = json.load(datafile)
    decks = raw_tour["decks"]
    if len(decks) < 8:
        shutil.move(t_file, join(base_path, useless_path))
    else:
        date = str(get_tournament_date(t_file))[0:10]
        os.rename(t_file, join(base_path, date + f[6:]))





