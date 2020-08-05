import pandas as pd
import numpy as np
from IPython.display import display

dataframe = pd.read_csv("/home/aicon/kunalS/workspace/csvTest/container_usage.csv")
print(dataframe.head(10))

np_array = dataframe.to_numpy()
print("************")
display(np_array)