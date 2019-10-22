import pandas as pd
import numpy as np
import matplotlib.pyplot as plt 
from statisticalAnalysis import stats

class plotting:

    def __init__(self):
        self.a = 1
    
    def plot(self):
        clusters = 10
        result = stats('20191015jtokarowski', 'Tracks20191014')
        result.kMeans(clusters)
        centers = result.centers
        X = ['acousticness', 'danceability', 'energy', 'instrumentalness','liveness','speechiness','valence']
        plotting.subcategorybar(X, centers)

        return

    def subcategorybar(X, vals, width=0.5):
        n = len(vals)
        _X = np.arange(len(X))
        for i in range(n):
            plt.bar(_X - width/2. + i/float(n)*width, vals[i],width=width/float(n), align="edge",label='cluster'+str(i))
        plt.xticks(_X, X)
        plt.legend()
        plt.savefig('test', format='png')
        plt.close()

#subcategorybar(X, centers)

#plt.show()