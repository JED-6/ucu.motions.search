import pandas as pd
import re

df = pd.read_excel("UCU Motions 2024-2006.xlsx")

def split_motion(text):
    splits_O = re.split("\n *(?:i+|[a-z]+|[0-9]+)\\. *",text)
    splits_T = []
    for s in range(0,len(splits_O)):
        splits_O[s] = re.sub("\n"," ",splits_O[s])
        splits_O[s] = re.sub(" *$","",splits_O[s])
        splits_T = splits_T + re.split("\\. *", splits_O[s])
        if len(splits_T[-1]) == 0:
            splits_T = splits_T[:-1]
    return(splits_T)


split_motions = {"Contents":[],"ID":[],"index":[]}
for m in range(0,len(df)):
    splits = split_motion(df.iloc[m,6])
    split_motions["Contents"] = split_motions["Contents"] + splits
    split_motions["ID"] = split_motions["ID"] + [df.iloc[m,11] for f in range(0,len(splits))]
split_motions["index"] = [f for f in range(0,len(split_motions["Contents"]))]
split_motions = pd.DataFrame(split_motions)
print(split_motions)
