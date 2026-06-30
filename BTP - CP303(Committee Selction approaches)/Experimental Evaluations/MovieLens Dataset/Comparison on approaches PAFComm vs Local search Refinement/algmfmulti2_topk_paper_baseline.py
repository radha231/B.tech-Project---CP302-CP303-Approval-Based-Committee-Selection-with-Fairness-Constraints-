import pandas as pd
import sys
import networkx as nx
import random

ballots_df = pd.read_csv("approval_ballot.csv")
movies_df = pd.read_csv("movie_attributes.csv")
movies_df["movie_id"] = movies_df["movie_id"].astype(int)

V = {}
for _, row in ballots_df.iterrows():
    user = f"v{int(row['user_id'])}"
    V[user] = {int(row["movie_id"])}

vote_counts = {}
for approvals in V.values():
    for m in approvals:
        vote_counts[m] = vote_counts.get(m, 0) + 1

Lv = []
Lc = []
for _, row in movies_df.iterrows():
    movie = row["movie_id"]
    if movie in vote_counts:
        Lv.append(vote_counts[movie])
        Lc.append((row["final_genre"], row["year_group"]))

a = [
    {"Horror": 2, "Comedy": 3}, 
    {"Old": 3, "New": 2}         
]

k = 5
def findAplusR(Lv, Lc, a, t, k):
    A = [set(), set()]
    for i, j in Lc:
        A[0].add(i)
        A[1].add(j)
    A = [list(A[0]), list(A[1])]
    w = []
    for i in range(len(Lv)):
        if Lv[i] < t:
            w.append(t - Lv[i])
        else:
            w.append((t - 1) - Lv[i])

    G = nx.DiGraph()
    G.add_node("Source", demand=-k)
    G.add_node("Destination", demand=k)
    for i in A[0]:
        G.add_edge("Source", i, capacity=a[0].get(i, 0))
    for j in A[1]:
        G.add_edge(j, "Destination", capacity=a[1].get(j, 0))
    for c in range(len(Lc)):
        i, j = Lc[c]
        dummy = f"{j}_{random.random()}"
        G.add_edge(i, dummy, weight=w[c], capacity=1)
        G.add_edge(dummy, j, weight=0, capacity=1)
    flowDict = nx.min_cost_flow(G)
    cost = nx.cost_of_flow(G, flowDict)
    costAR = cost
    for wc in w:
        if wc < 0:
            costAR -= wc
    return costAR

def AlgMFMulti2(Lv, Lc, a, k):
    OPT_ar = float('inf')
    OPT_t = -1
    Lvunq = list(set(Lv))
    Lvunq.sort(reverse=True)

    for i in range(len(Lvunq)):
        cost1 = findAplusR(Lv, Lc, a, Lvunq[i], k)
        cost2 = findAplusR(Lv, Lc, a, Lvunq[i] + 1, k)
        cost3 = float('inf')
        ind3 = -1
        if i < len(Lvunq) - 1:
            cost3 = findAplusR(Lv, Lc, a, Lvunq[i+1] - 1, k)
            ind3 = Lvunq[i+1]
        cost, t = min(
            (cost1, Lvunq[i]),
            (cost2, Lvunq[i] + 1),
            (cost3, ind3 - 1)
        )
        if cost < OPT_ar:
            OPT_ar = cost
            OPT_t = t
    return OPT_ar, OPT_t

with open("code2_output.txt", "w") as f:
    original_stdout = sys.stdout
    sys.stdout = f
    print("Algorithm 4 (AlgMFMulti2) Result")
    OPT_ar, OPT_t = AlgMFMulti2(Lv, Lc, a, k)
    print("Minimum A+R (fairness cost):", OPT_ar)
    print("Best threshold t:", OPT_t)
    print("Number of candidates:", len(Lv))
    print("k:", k)
    sys.stdout = original_stdout
    
print("Results saved to code2_output.txt")
