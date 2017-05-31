import os
import shutil
from pprint import pprint
from os import listdir
from os.path import isfile, join
import json


basepath = "C:\\Users\\pitu\\Desktop\\DATA\\MTGOprices\\Modern\\"
treshold = 0.3

subdirs = next(os.walk(basepath))[1]
for subdir in subdirs:
    subpath = basepath + str(subdir)

    useless_path = "not_significant"
    if not os.path.exists(join(subpath, useless_path)):
        os.makedirs(join(subpath, useless_path))

    price_files = [f for f in listdir(subpath) if isfile(join(subpath, f))]

    for price_file in price_files:
        with open(join(subpath, price_file)) as datafile:
            rawjson = json.load(datafile)
        timePriceList = rawjson["data"]
        only_prices = [x[1] for x in timePriceList]
        if max(only_prices) < treshold:
            shutil.move(join(subpath, price_file), join(subpath, useless_path))

