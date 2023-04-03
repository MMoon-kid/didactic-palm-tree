import numpy as np
import pandas as pd

frame = pd.read_excel(
    "2023_MCM_Problem_Y_Boats.xlsx", dtype={"Variant": str, "Country/Region/State": str}
)
frame["Variant"] = [f"{i} {j}" for i, j in zip(frame["Make"], frame["Variant"])]
# print(frame)
s, n = np.unique(frame["Variant"], return_counts=True)
s, n = s[n.argsort()], np.sort(n)
# print(s[:20])

def splitBy(x: list, n: int):
    l = len(x)
    return [x[int(i / n * l) : int((i + 1) / n * l)] for i in range(n)]
