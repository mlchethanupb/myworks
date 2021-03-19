#Calculates RMSE and R^2 error between used and predicted disk usage

import pandas as pd
import numpy as np
import math
from sklearn.metrics import mean_squared_error, r2_score
used_storage = pd.read_csv("sfc.csv")
du = used_storage['used']
pu = used_storage['predicted']
#print(du)
#print(pu)

MSE = np.square(np.subtract(du,pu)).mean() 
RMSE = math.sqrt(MSE)
print("Root Mean Square Error:\n")
print(RMSE)

r2=r2_score(du,pu)
print("R Square Error:\n")
print(r2)
