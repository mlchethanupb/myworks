#performs 5 fold cross validation of SVR model over a range of hyper-parameters (gamma, C and epsilon)
#and returns the best model and parameters

import pandas as pd
import numpy as np
from scipy.interpolate import griddata
from matplotlib import font_manager as fm, rcParams  
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from sklearn import svm
from sklearn.svm import SVC
import pickle
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import KFold
from sklearn.model_selection import GridSearchCV



df = pd.read_csv("squid_all2.csv")
parameters = {'kernel': ['rbf'], 'C':[0.001,0.01,0.1,1,10,100,1000,10000,100000],'gamma': [1e-3, 0.005,0.01,0.05, 0.1,0.5],'epsilon':[0.001, 0.005, 0.01, 0.05, 0.1, 0.3, 0.5, 1,3,5]}
svr = svm.SVR()
print("Tuning hyper-parameters")



S= df.loc[:,['Total Time/sec','Cache Disk/mb']].values
t= df.loc[:,'Disk Usage/mb']
cv = GridSearchCV(svr, parameters, verbose=2, cv=5)
cv.fit(S,t)

file = open("validation.txt","a")
file.write("'Best score :'\n")
file.write(str(cv.best_score_))
file.write("\n")
file.write("'Best C:'\n")
file.write(str(cv.best_estimator_.C))
file.write("\n")
file.write("'Best Kernel:'\n")
file.write(str(cv.best_estimator_.kernel))
file.write("\n")
file.write("'Best Gamma:'\n")
file.write(str(cv.best_estimator_.gamma))
file.write("\n")
file.write("'Best Epsilon:'\n")
file.write(str(cv.best_estimator_.epsilon))
file.write("\n")
file.close()
