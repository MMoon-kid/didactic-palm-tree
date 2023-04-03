import numpy as np, pandas as pd
import requests, bs4, multiprocessing as mp
import sys, dataclasses, tqdm
import matplotlib.pyplot as plt
from sklearn.neural_network import MLPRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split, learning_curve, ShuffleSplit
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from collections import Counter
from itertools import product
from time import time
from SALib.sample.sobol import sample
from SALib.analyze.sobol import analyze

import warnings
warnings.filterwarnings("ignore")
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号


def mape(actual: np.ndarray, pred: np.ndarray):
    return np.mean(np.abs((actual - pred) / actual))


def mergeTable(key: str):
    data1 = pd.read_excel('2023_MCM_Problem_Y_Boats.xlsx', sheet_name=key)
    data2 = pd.read_excel('2023_MCM_Problem_Y_Boats.xlsx', sheet_name=f'{key}_1')
    data3 = pd.read_excel('2023_MCM_Problem_Y_Boats.xlsx', sheet_name=f'{key}_2')
    for i in ['平均货物吞吐量（吨）', 'GDP（亿美元）', '人均GDP（美元）', '物流总成本占GDP的平均比例']:
        data3[i] = data3[i].apply(lambda x: np.NaN if x == '-' else x)
    getx = lambda x: str(x['Make']) + ' ' + str(x['Variant'])
    data1['Make Variant'] = data1.apply(getx, axis=1)
    data2 = data2.drop_duplicates(keep='first', subset='型号')
    data2['型号'] = data2['型号'].apply(lambda x: x.replace(' ', ''))
    data1['Make Variant'] = data1['Make Variant'].apply(lambda x: x.replace(' ', ''))
    data = pd.merge(data1, data2, how='left', left_on='Make Variant', right_on='型号')

    def tra(x):
        try:
            return x.lower().replace(' ', '')
        except:
            return x

    data3['城市/地区'] = data3['城市/地区'].apply(tra)
    data['Country/Region/State '] = data1['Country/Region/State '].apply(tra)
    data = pd.merge(
        data, data3, how='left', left_on='Country/Region/State ', right_on='城市/地区'
    )
    data.columns = [
        'Make',
        'Variant',
        'Length \n(ft)',
        'Geographic Region',
        'Country/Region/State ',
        'Listing Price (USD)',
        'Year',
        'Make Variant',
        'Make Variant2',
        'LWL (ft)',
        'Beam (ft)',
        'Draft (ft)',
        'Displacement (lbs)',
        'Sail Area (sq ft)',
        'City/Region',
        'Average cargo throughput (tons)',
        'GDP (USD billion)',
        'GDP per capita (USD)',
        'Average ratio of total logistics costs to GDP',
    ]
    data = data[
        [
            'Make',
            'Variant',
            'Length \n(ft)',
            'Geographic Region',
            'Country/Region/State ',
            'Listing Price (USD)',
            'Year',
            'Make Variant',
            'LWL (ft)',
            'Beam (ft)',
            'Draft (ft)',
            'Displacement (lbs)',
            'Sail Area (sq ft)',
            # 'Average cargo throughput (tons)',
            'GDP (USD billion)',
            'GDP per capita (USD)',
            # 'Average ratio of total logistics costs to GDP',
        ]
    ]
    return data


def freqTable(table, key):
    return pd.DataFrame(
        sorted(Counter(table[key]).items(), key=lambda x: x[1]),
        columns=[key, f'{key} num'],
    )


def train(model, X: np.ndarray, Y: np.ndarray) -> None:
    t0 = time()
    model.fit(X, Y)
    Y_pred = model.predict(X)
    print(f"model: {type(model).__name__}:")
    print("MAPE: {:.3f}".format(mape(Y_pred, Y)))
    print("r^2 score", r2_score(Y, Y_pred))
    print(f"cost time: {time() - t0} s\n")


def sensitiveAnalyze(func, sample_n: int = 10, **args: tuple[float, float]):
    problem = {
        "num_vars": len(args),
        "names": list(args),
        "bounds": [args[i] for i in args],
    }
    param_values = sample(problem, 2**sample_n)
    Y = func(param_values)
    return analyze(problem, Y)


def cov(a: np.ndarray, b: np.ndarray):
    """协方差"""
    return ((a - a.mean()) * (b - b.mean())).mean()


def pearson(a: np.ndarray, b: np.ndarray):
    """皮尔逊相关系数"""
    return cov(a, b) / (a.std() * b.std())
