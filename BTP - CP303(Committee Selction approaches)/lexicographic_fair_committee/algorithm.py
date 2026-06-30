from itertools import combinations
import matplotlib.pyplot as plt

def lexicographic_fair_committee(voters, approvals_per_round, candidates_per_round, k, beta=10):
    z = {v:0 for v in voters}
    committees = []
    welfare_history = []
    fairness_history = []

    for t in range(len(approvals_per_round)):
        approvals = approvals_per_round[t]
        candidates = candidates_per_round[t]
        best_score = None
        best_committee = None
        best_y = None
        for C in combinations(candidates, k):
            y = {}
            for v in voters:
                if any(c in approvals[v] for c in C):
                    y[v] = 1
                else:
                    y[v] = 0

            z_new = {v: z[v] + y[v] for v in voters}
            W = sum(y.values())
            z_sorted = sorted(z_new.values())
            fairness_score = sum(beta**(len(voters)-i-1) * z_sorted[i]
                           for i in range(len(voters)))
            
            score = W + fairness_score
            if best_score is None or score > best_score:
                best_score = score
                best_committee = C
                best_y = y
                best_z = z_new
                best_W = W

        committees.append(best_committee)
        z = best_z
        lambda_fair = min(z.values())
        welfare_history.append(best_W)
        fairness_history.append(lambda_fair)
        print(f"Round {t+1}")
        print("Selected committee:", best_committee)
        print("Welfare:", best_W)
        print("Fairness (min representation λ):", lambda_fair)
        print("Representation vector:", z)
        print("------")

    return committees, welfare_history, fairness_history

voters = ["v1","v2","v3","v4","v5","v6"]
candidates_per_round = [
["a","b","c","d","e","f","g","h"],
["b","c","d","e","f","g","h","i"],
["c","d","e","f","g","h","i"],
["c","d","e","f","g","h","i"]
]

approvals_per_round = [
{
"v1":["a"],
"v2":["b"],
"v3":["c","d"],
"v4":["e","f"],
"v5":["g","h"],
"v6":["a","c","e"]
},
{
"v1":["c"],
"v2":["b"],
"v3":["d","e"],
"v4":["f","g"],
"v5":["h","i"],
"v6":["c","f","i"]
},
{
"v1":["c"],
"v2":["d"],
"v3":["e","f"],
"v4":["g","h"],
"v5":["i","c"],
"v6":["d","g","i"]
},
{
"v1":["c"],
"v2":["d"],
"v3":["e","g"],
"v4":["f","h"],
"v5":["i","e"],
"v6":["c","f","i"]
}
]

committees, welfare, fairness = lexicographic_fair_committee(
    voters,
    approvals_per_round,
    candidates_per_round,
    k=3,
    beta=10
)

print("Final Committees:", committees)
