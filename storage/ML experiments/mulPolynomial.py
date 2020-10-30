import pandas as pd
import numpy as np
from matplotlib import cm
from matplotlib import pyplot
from scipy.interpolate import griddata
from mpl_toolkits.mplot3d import Axes3D
from sklearn import linear_model
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import PolynomialFeatures

df = pd.read_csv("E:\\t1.csv")

#S = df[['Kafka Total Space(mb)', 'CPU Utilization(%)', 'Message Size(bytes)']]
S= df.iloc[:,-9:-6].values
t = df['Kafka Total Space(mb)']

regr = linear_model.LinearRegression()
polynomial_features= PolynomialFeatures(degree=4)
S_poly = polynomial_features.fit_transform(S)
regr.fit(S_poly, t)
zp = regr.predict(S_poly)
rmse = np.sqrt(mean_squared_error(t,zp))
r2 = r2_score(t,zp)
print("RMSE is:",rmse)
print("R2 is:",r2)

x = S[:, 0]
y = S[:, 1]
p = S[:, 2]
#print("X is:",x)
#print("y is:",y)
#print("p is:",p)
z = t
#print("Z is:",z)

xi = np.linspace(min(x), max(x))
yi = np.linspace(min(y), max(y))
X, Y = np.meshgrid(xi, yi)
x_y = np.c_[x.ravel(), y.ravel()]
ZP = griddata(x_y, zp.ravel(), (X, Y))

fig = pyplot.figure()
ax = fig.gca(projection='3d')
surf = ax.plot_surface(X, Y, ZP, rstride=1, cstride=1, facecolors=cm.viridis(ZP/3200), linewidth=0, antialiased=True)
ax.scatter(x, y, z,color='b')
ax.set_zlim3d(np.min(z), np.max(z))
colorscale = cm.ScalarMappable(cmap=cm.viridis)
colorscale.set_array(z)
ax.set_title('Polynomial Regression (Order=4)')
ax.set_xlabel('Response Time / (ms)')
ax.set_zlabel('Storage Consumption (Mb)')
ax.set_ylabel('Message Size (Bytes)')
fig.colorbar(colorscale,label='Storage Consumption (Mb)')
pyplot.show()
