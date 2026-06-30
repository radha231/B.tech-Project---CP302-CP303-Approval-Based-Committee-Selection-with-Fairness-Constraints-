import pandas as pd
import ast
import random
import time

random.seed(42)
ballots_df = pd.read_csv("approval_ballots.csv")
movies_df = pd.read_csv("movie_attributes.csv")
movies_df["movie_id"] = movies_df["movie_id"].astype(int)

C = set(movies_df["movie_id"].tolist())

V = {}
for _, row in ballots_df.iterrows():
    user = f"v{int(row['user_id'])}"
    V[user] = set(ast.literal_eval(row["movie_id"]))

genre_groups = {
    genre: set(movies_df[movies_df["final_genre"] == genre]["movie_id"])
    for genre in movies_df["final_genre"].unique()
}

year_groups = {
    "Old": set(movies_df[movies_df["year_group"] == "Old"]["movie_id"]),
    "New": set(movies_df[movies_df["year_group"] == "New"]["movie_id"]),
}

groups = {**genre_groups, **year_groups}

for g in genre_groups:
    for y in year_groups:
        groups[f"{g}_{y}"] = genre_groups[g] & year_groups[y]

R_g = {"Horror": 2, "Comedy": 1, "Old": 1, "Horror_Old": 1}
k = 5
lambda_ = 1
mu = 1

group_totals = {
    g: sum(len(V[v] & groups[g]) for v in V)
    for g in groups
}

def pav_utility(S):
    return sum(
        sum(1.0 / j for j in range(1, len(S & V[v]) + 1))
        for v in V
    )

def penrep(S):
    return sum(
        max(0, R_g[g] - len(S & groups[g]))
        for g in R_g
    )

def max_min(S):
    values = []
    for g in R_g:
        total = sum(len(V[v] & S & groups[g]) for v in V)
        denom = max(1, group_totals[g])
        values.append(total / denom)
    return min(values)


def count_sat(S):
    return sum(1 for g in R_g if len(S & groups[g]) >= R_g[g])

def greedy():
    S = set()
    for _ in range(k):
        best_c, best_score = None, -1e9

        for c in C - S:
            S_new = S | {c}
            score = (
                pav_utility(S_new)
                - lambda_ * penrep(S_new)
                + mu * max_min(S_new)
            )
            if score > best_score:
                best_score, best_c = score, c

        S.add(best_c)
    return S

def local_search(max_iters=10, sample_voters=20, sample_items=20):
    V_current = {v: set(apps) for v, apps in V.items()}

    for it in range(max_iters):
        print(f"\n[ITER {it+1}]")

        S = greedy()
        base_key = (-penrep(S), count_sat(S), max_min(S), pav_utility(S))

        print(f"[BASE] Pen={-base_key[0]}, Sat={base_key[1]}, MM={base_key[2]:.4f}")

        voters_sample = random.sample(list(V_current.keys()),
                                      min(sample_voters, len(V_current)))

        improved = False
        checked = 0
        start = time.time()
        print("111111")
        for voter in voters_sample:
            approvals = V_current[voter]
            
            for out_c in list(approvals)[:sample_items]:
                for in_c in list(C - approvals)[:sample_items]:

                    checked += 1
                    print("check= "+ str(checked))
                    if checked % 200 == 0:
                        print(f"[SEARCH] {checked} swaps checked | {time.time()-start:.1f}s")

                    V_new = {u: set(apps) for u, apps in V_current.items()}
                    V_new[voter].discard(out_c)
                    V_new[voter].add(in_c)

                    S_new = greedy()

                    new_key = (
                        -penrep(S_new),
                        count_sat(S_new),
                        max_min(S_new),
                        pav_utility(S_new),
                    )

                    if new_key > base_key:
                        print(f"[IMPROVE] voter={voter}, {out_c}->{in_c}")
                        V_current = V_new
                        improved = True
                        break

                if improved:
                    break
            if improved:
                break

        if not improved:
            print("[STOP] No improvement found")
            break

    return V_current

print("\nINITIAL GREEDY")
S_init = greedy()
print("Initial:", S_init)

print("\nLOCAL SEARCH")
V_final = local_search(max_iters=10)

print("\nFINAL RESULT")
S_final = greedy()

print("Final Committee:", S_final)
print("Penalty:", penrep(S_final))
print("Satisfied:", count_sat(S_final), "/", len(R_g))
print("Max-Min:", max_min(S_final))
print("Utility:", pav_utility(S_final))
