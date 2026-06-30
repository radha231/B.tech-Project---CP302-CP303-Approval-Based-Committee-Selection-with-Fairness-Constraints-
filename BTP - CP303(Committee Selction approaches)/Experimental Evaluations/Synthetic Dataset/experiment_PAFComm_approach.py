from collections import defaultdict
C = ["c1", "c2", "c3", "c4", "c5", "c6"]
V = {
    "v1": {"c1", "c2", "c5"},
    "v2": {"c2", "c3", "c6"},
    "v3": {"c4", "c5", "c6"},
    "v4": {"c1", "c3", "c4", "c5"},
    "v5": {"c2", "c5", "c6"},
    "v6": {"c1", "c2", "c3", "c4"},
    "v7": {"c4", "c6"}
}
groups = {
    "Male": {"c1", "c2"},
    "Female": {"c3", "c4", "c5", "c6"},
    "White Male": {"c1"},
    "Black Male": {"c2"},
    "White Female": {"c3", "c4"},
    "Black Female": {"c5", "c6"},
    "White": {"c1", "c3", "c4"},
    "Black": {"c2", "c5", "c6"}
}
R_g = {
    "Black Male": 1,
    "White Female": 1,
    "Black Female": 2
}

k = 4
lambda_ = 2
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
print("Committee:", S_final)
print("PAV:", pav_utility(S_final))
print("Penalty:", penrep(S_final))
print("MM:", max_min(S_final))

def greedy_with_tracking(lambda_, mu):
    S = set()
    pav_progress = []
    pen_progress = []
    mm_progress = []
    score_progress = []
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
        pav_progress.append(pav_utility(S))
        pen_progress.append(penrep(S))
        mm_progress.append(max_min(S))
        score_progress.append(
            pav_utility(S) - lambda_ * penrep(S) + mu * max_min(S)
        )
    return pav_progress, pen_progress, mm_progress, score_progress
lambda_values = [0, 1, 2, 3]
import matplotlib.pyplot as plt
plt.figure()
for lam in lambda_values:
    _, _, _, score = greedy_with_tracking(lam, mu=1)
    plt.plot(range(1, k+1), score, marker='o', label=f"λ={lam}")
plt.xlabel("Step")
plt.ylabel("Score")
plt.title("Score Progression for Different Lambda")
plt.legend()
plt.grid()
plt.show()
mu_values = [0, 1, 2, 3]
plt.figure()
for mu_val in mu_values:
    _, _, _, score = greedy_with_tracking(lambda_=2, mu=mu_val)
    plt.plot(range(1, k+1), score, marker='o', label=f"μ={mu_val}")
plt.xlabel("Step")
plt.ylabel("Score")
plt.title("Score Progression for Different Mu")
plt.legend()
plt.grid()
plt.show()
