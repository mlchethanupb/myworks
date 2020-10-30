import os
import pandas as pd
import numpy as np
from matplotlib import cm
from matplotlib import pyplot
from scipy.interpolate import griddata
from mpl_toolkits.mplot3d import Axes3D
from sklearn.metrics import mean_squared_error, r2_score
from matplotlib import font_manager as fm, rcParams 


df = pd.read_csv("E:\\t1.csv")

#S = df[['Kafka Total Space(mb)', 'CPU Utilization(%)', 'Message Size(bytes)']]
S= df.iloc[:,-9:-6].values
t = df['Kafka Total Space(mb)']

#S = S.reshape((len(S),1))
#print(S.shape)

#t = t.reshape(len(t),1)
#print(t.shape)
#feature scaling
from sklearn.preprocessing import StandardScaler
#sc_S = StandardScaler()
#sc_t = StandardScaler()
#S2 = sc_S.fit_transform(S)
#t2 = sc_t.fit_transform(t)


#fitting the SVR to the dataset
from sklearn.svm import SVR
regressor = SVR(kernel = 'rbf',C=1e4, gamma=0.1)
regressor.fit(S, t)



#displaying the 3D graph
x = S[:, 0]
y = S[:, 1]
p = S[:, 2]

z = t
zp = regressor.predict(S) #the predictions
rmse =np.sqrt(mean_squared_error(z,zp))
r2 = r2_score(z,zp)
print("RMSE:",rmse)
print("R2:",r2)

xi = np.linspace(min(x), max(x))
yi = np.linspace(min(y), max(y))
X, Y = np.meshgrid(xi, yi)
lon_lat = np.c_[x.ravel(), y.ravel()]
ZP = griddata(lon_lat, zp.ravel(), (X, Y))

#plotting
fig = pyplot.figure()
ax = fig.gca(projection='3d')
surf = ax.plot_surface(X, Y, ZP, rstride=1, cstride=1, facecolors=cm.viridis(ZP/3200), linewidth=0, antialiased=True)
ax.scatter(x, y, z,color='b')
ax.set_zlim3d(np.min(z), np.max(z))
colorscale = cm.ScalarMappable(cmap=cm.viridis)
colorscale.set_array(z)
fig.colorbar(colorscale, label='Storage Consumption (Mb)')
ax.set_xlabel('Response Time / (ms)')
ax.set_zlabel('Storage Consumption (Mb)')
ax.set_ylabel('Message Size (Bytes)')
ax.set_title('Support Vector Regression(kernel=RBF,gamma=0.1)')
pyplot.show()