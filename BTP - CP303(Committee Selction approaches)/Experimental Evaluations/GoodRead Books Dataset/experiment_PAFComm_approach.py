import pandas as pd
import ast
import matplotlib.pyplot as plt

ballots_df = pd.read_csv("approval_ballots.csv")
books_df = pd.read_csv("book_attributes.csv")
books_df["book_id"] = books_df["book_id"].astype(int)
C = set(books_df["book_id"].tolist())
V = {}

for _, row in ballots_df.iterrows():
    user = f"v{int(row['user_id'])}"
    books = set(ast.literal_eval(row["book_id"]))
    V[user] = books

year_groups = {
    "Old": set(books_df[books_df["year_group"] == "Old"]["book_id"]),
    "New": set(books_df[books_df["year_group"] == "New"]["book_id"]),
}

pop_groups = {}
for p in books_df["pop_group"].unique():
    pop_groups[str(p)] = set(
        books_df[books_df["pop_group"] == p]["book_id"]
    )

author_groups = {
    "TopAuthor": set(books_df[books_df["author_group"] == "TopAuthor"]["book_id"]),
    "Other": set(books_df[books_df["author_group"] == "Other"]["book_id"]),
}

groups = {}
groups.update(year_groups)
groups.update(pop_groups)
groups.update(author_groups)

for y in year_groups:
    for p in pop_groups:
        groups[f"{y}_{p}"] = year_groups[y] & pop_groups[p]

for y in year_groups:
    for a in author_groups:
        groups[f"{y}_{a}"] = year_groups[y] & author_groups[a]

for p in pop_groups:
    for a in author_groups:
        groups[f"{p}_{a}"] = pop_groups[p] & author_groups[a]

for y in year_groups:
    for p in pop_groups:
        for a in author_groups:
            groups[f"{y}_{p}_{a}"] = (
                year_groups[y] & pop_groups[p] & author_groups[a]
            )

R_g = {
    "Old": 1,
    "New_TopAuthor": 1,
    "4": 1,         
    "Old_4": 1,
    "Old_4_TopAuthor": 1
}

k = 8
lambda_ = 50
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
    return sum(len(approvals & S & G) for approvals in V.values())

def normalized_group_satisfaction(S, G):
    max_possible = sum(len(approvals & G) for approvals in V.values())
    if max_possible == 0:
        return 0
    return group_satisfaction(S, G) / max_possible

def max_min(S):
    return min(normalized_group_satisfaction(S, groups[g]) for g in R_g)

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
print("Selected Books:", S_final)
print("PAV:", pav_utility(S_final))
print("Penalty:", penrep(S_final))
print("MM:", max_min(S_final))

print("\nSelected Book Details:")
print(books_df[books_df["book_id"].isin(S_final)])

def count_satisfied_constraints(S):
    return sum(1 for g in R_g if len(S & groups[g]) >= R_g[g])

lambda_values = list(range(10, 70, 10))
fairness_percentages = []

total_constraints = len(R_g)

for lam in lambda_values:
    print(f"\n===== Running for lambda = {lam} =====")

    lambda_ = lam
    S = greedy()

    satisfied = count_satisfied_constraints(S)
    fairness = (satisfied / total_constraints) * 100
    fairness_percentages.append(fairness)

    print(f"Selected set: {S}")
    print(f"Fairness: {fairness:.2f}%")

plt.figure()
plt.plot(lambda_values, fairness_percentages, marker='o')
plt.xlabel("Lambda (λ)")
plt.ylabel("Fairness (%)")
plt.title("Fairness vs Lambda")
plt.grid()
plt.show()
