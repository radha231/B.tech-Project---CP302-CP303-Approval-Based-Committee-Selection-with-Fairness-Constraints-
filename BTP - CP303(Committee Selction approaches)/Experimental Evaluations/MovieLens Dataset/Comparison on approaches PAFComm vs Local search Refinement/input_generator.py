import pandas as pd

df = pd.read_csv("u.data", sep='\t', header=None,
                 names=['userId', 'movieId', 'rating', 'timestamp'])
df = df.sort_values(['userId', 'rating'], ascending=[True, False])
df_single = df.groupby('userId').first().reset_index()
df_single = df_single[['userId', 'movieId']]
df_single.to_csv("approval_ballot.csv", index=False)

print("File saved as approval_ballot.csv")