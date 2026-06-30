import pandas as pd
import ast
import matplotlib.pyplot as plt

ballots_df = pd.read_csv("approval_ballots.csv")
movies_df = pd.read_csv("movie_attributes.csv")
movies_df["movie_id"] = movies_df["movie_id"].astype(int)
C = set(movies_df["movie_id"].tolist())
V = {}

for _, row in ballots_df.iterrows():
    user = f"v{int(row['user_id'])}"
    movies = set(ast.literal_eval(row["movie_id"]))
    V[user] = movies

genre_groups = {}
for genre in movies_df["final_genre"].unique():
    genre_groups[genre] = set(
        movies_df[movies_df["final_genre"] == genre]["movie_id"]
    )

year_groups = {
    "Old": set(movies_df[movies_df["year_group"] == "Old"]["movie_id"]),
    "New": set(movies_df[movies_df["year_group"] == "New"]["movie_id"]),
}

groups = {}
groups.update(genre_groups)
groups.update(year_groups)

for genre in genre_groups:
    for year in year_groups:
        group_name = f"{genre}_{year}"
        groups[group_name] = genre_groups[genre] & year_groups[year]

R_g = {
    "Horror": 2,
    "Comedy": 1,
    "Old": 1,
    "Horror_Old": 1  
}
k = 5
lambda_ = 110
mu = 1

def pav_utility(S):
    total = 0
    for approvals in V.values():
        t = len(S & approvals)
        total += sum(1.0 / j for j in range(1, t + 1))
    return total

def penrep(S):
    penalty = 0
    for g in R_g:
        members = groups[g]
        shortfall = max(0, R_g[g] - len(S & members))
        penalty += shortfall
    return penalty

def group_satisfaction(S, G):
    total = 0
    for approvals in V.values():
        total += len(approvals & S & G)
    return total

def normalized_group_satisfaction(S, G):
    max_possible = sum(len(approvals & G) for approvals in V.values())
    if max_possible == 0:
        return 0
    return group_satisfaction(S, G) / max_possible

def max_min(S):
    values = []
    for g in R_g:
        G = groups[g]
        values.append(normalized_group_satisfaction(S, G))
    return min(values)

def greedy():
    S = set()
    print("\n===== GREEDY START =====\n")
    for step in range(k):
        best_c = None
        best_score = -1e9
        print(f"Step {step+1}:")

        for c in C:
            if c in S:
                continue
            S_new = S | {c}
            delta_U = pav_utility(S_new) - pav_utility(S)
            delta_pen = penrep(S_new) - penrep(S)
            delta_mm = max_min(S_new) - max_min(S)
            score = delta_U - lambda_ * delta_pen + mu * delta_mm
            print(f"{c}: ΔU={delta_U:.3f}, ΔPen={delta_pen}, ΔMM={delta_mm:.3f}, Score={score:.3f}")
            if score > best_score:
                best_score = score
                best_c = c
        print(f"--> Selected: {best_c}\n")
        S.add(best_c)
    return S

S_final = greedy()
print("===== FINAL RESULT =====")
print("Selected Movies:", S_final)
print("PAV:", pav_utility(S_final))
print("Penalty:", penrep(S_final))
print("MM:", max_min(S_final))
print("\nSelected Movie Details:")
print(movies_df[movies_df["movie_id"].isin(S_final)])


def count_satisfied_constraints(S):
    satisfied = 0
    for g in R_g:
        if len(S & groups[g]) >= R_g[g]:
            satisfied += 1
    return satisfied

lambda_values = list(range(10, 70, 10))
fairness_percentages = []

total_constraints = len(R_g)

for lam in lambda_values:
    print(f"\n===== Running for lambda = {lam} =====")
    lambda_ = lam  
    S = set()
    for step in range(k):
        best_c = None
        best_score = -1e9
        for c in C:
            if c in S:
                continue
            S_new = S | {c}
            delta_U = pav_utility(S_new) - pav_utility(S)
            delta_pen = penrep(S_new) - penrep(S)
            delta_mm = max_min(S_new) - max_min(S)
            score = delta_U - lambda_ * delta_pen + mu * delta_mm
            if score > best_score:
                best_score = score
                best_c = c
        S.add(best_c)
    satisfied = count_satisfied_constraints(S)
    fairness = (satisfied / total_constraints) * 100
    fairness_percentages.append(fairness)
    print(f"Selected set: {S}")
    print(f"Satisfied constraints: {satisfied}/{total_constraints}")
    print(f"Fairness: {fairness:.2f}%")

plt.figure()
plt.plot(lambda_values, fairness_percentages, marker='o')
plt.xlabel("Lambda (λ)")
plt.ylabel("Fairness (%)")
plt.title("Fairness vs Lambda")
plt.grid()
plt.show()
