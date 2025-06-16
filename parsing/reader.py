import pandas as pd

files = (
    "2gis",
    "flamp",
    "yandex",
    "yell"
)

dfs = []
for file_name in files:
    dfs.append(pd.read_csv(f"{file_name}_reviews.csv"))

data = pd.concat(dfs, ignore_index=True)
data.drop(data.columns[0], axis=1, inplace=True)

print(data)
print(data.iloc[-1])