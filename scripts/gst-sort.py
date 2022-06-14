import matplotlib
from numpy.lib.twodim_base import mask_indices
import pandas as pd
import glob
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from pandas.io.pytables import IndexCol
import os, os.path
import math
import sys
import json 

# Take an experiment number and return its dataframe
def get_frame(num):
    for filename in glob.glob(num):
        df = pd.read_json(filename, typ='series')
    return df    

# default 5 
base = '/home/lyn/filter/output/gst/'

# Check for experiment folder in CL
if len(sys.argv) < 3:
    print("Missing folder and/or number of client arguments")
    exit(0)
    
folder = sys.argv[1]
exper_total = sys.argv[2]

if not os.path.isdir(base + folder):
    print("This folder doesn't exist.")
    exit(1)

# main 
exper = []
filelist = glob.glob(base + folder + "/*.json")

for x in range(len(filelist)):
    exper.append(get_frame(filelist[x]))
df_concat = pd.concat(exper)
df_concat = df_concat.groupby(df_concat.index)

output = df_concat.mean().to_json()
output = json.loads(output)
failed = {"Failed streams":(int(exper_total) - len(filelist))}
output.update(failed)
with open(base + folder + "/combined.txt", 'w') as f:
    f.write(json.dumps(output))