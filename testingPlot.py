import pandas as pd
import numpy as np
import matplotlib.pyplot as plt 
from statisticalAnalysis import stats

clusters = 10
result = stats('20191015jtokarowski', 'Tracks20191014')
result.kMeans(clusters)
centers = result.centers

X = ['acousticness', 'danceability', 'energy', 'instrumentalness','liveness','speechiness','valence']

def subcategorybar(X, vals, width=0.5):
    n = len(vals)
    _X = np.arange(len(X))
    for i in range(n):
        plt.bar(_X - width/2. + i/float(n)*width, vals[i], 
                width=width/float(n), align="edge",label='cluster'+str(i))   
    plt.xticks(_X, X)
    plt.legend()

subcategorybar(X, centers)

plt.show()