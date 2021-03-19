#creates sub-models using the cross validated parameters both for SVR and polynomial regressor

import pandas as pd
import numpy as np
from scipy.interpolate import griddata
from mpl_toolkits.mplot3d import Axes3D
from sklearn.metrics import mean_squared_error, r2_score
from matplotlib import font_manager as fm, rcParams  
from sklearn import linear_model
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import PolynomialFeatures
from sklearn.model_selection import train_test_split
from sklearn.svm import SVR
import pickle


df = pd.read_csv("squid_all2.csv",encoding="ISO-8859-1")
df = df.reset_index()
S= df.loc[:,['Total Time/sec','Ingestion Rate/sec']].values
t= df.loc[:,'Cache Disk/mb']


S_train, S_test, t_train, t_test = train_test_split(S, t, test_size=0.2)
regressor= SVR(kernel='rbf', C=1000, gamma=0.1, epsilon=0.005)
#regressor2=linear_model.LinearRegression()
#polynomial_features= PolynomialFeatures(degree=3)
#S_poly = polynomial_features.fit_transform(S_train)
#S_poly_t = polynomial_features.fit_transform(S_test)



regressor.fit(S_train, t_train)
z = t_train
zp = regressor.predict(S_train)
rmse =np.sqrt(mean_squared_error(z,zp))
r2 = r2_score(z,zp)
print('total disk')
print('error on train data:')
print('rmse:',rmse)
print('r2:',r2)

z2 = t_test
zp2 = regressor.predict(S_test)
rmse2 =np.sqrt(mean_squared_error(z,zp))
r21 = r2_score(z2,zp2)

print('error on test data:')
print('rmse:',rmse2)
print('r2:',r21)



file = 'model-cachedisk'
pickle.dump(regressor, open(file, 'wb'))


