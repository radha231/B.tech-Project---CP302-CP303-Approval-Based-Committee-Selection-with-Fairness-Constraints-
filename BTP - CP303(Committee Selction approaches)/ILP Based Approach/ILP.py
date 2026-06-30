import os
import pulp
import numpy as np
import matplotlib.pyplot as plt


# -----------------------------
# DATA PARSER
# -----------------------------

def parse_soc_file(filepath):
    candidates = set()
    ballots = []

    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            if line.startswith("# ALTERNATIVE NAME"):
                parts = line.split()
                try:
                    num = int(parts[3].replace(":", ""))
                    candidates.add(num)
                except:
                    pass

            elif not line.startswith("#"):
                parts = line.split(":")
                if len(parts) == 2:
                    order = [int(x.strip()) for x in parts[1].split(",") if x.strip()]
                    ballots.append(set(order))

    return sorted(list(candidates)), ballots


# -----------------------------
# ILP FORMULATION
# -----------------------------

def solve_temporal_ilp(candidates, ballots, rounds=10, k=1):

    voters = list(range(len(ballots)))
    C = candidates
    T = list(range(rounds))

    epsilon = 1e-4

    prob = pulp.LpProblem("TemporalVoting", pulp.LpMaximize)

    x = pulp.LpVariable.dicts("x", (C, T), 0, 1, pulp.LpBinary)
    y = pulp.LpVariable.dicts("y", (voters, T), 0, 1, pulp.LpBinary)
    z = pulp.LpVariable.dicts("z", (voters, T), 0)
    lam = pulp.LpVariable("lambda", 0)

    prob += pulp.lpSum(y[i][t] for i in voters for t in T) + epsilon * lam

    for t in T:
        prob += pulp.lpSum(x[p][t] for p in C) == k

    for i in voters:
        for t in T:
            approved = ballots[i]

            prob += y[i][t] <= pulp.lpSum(x[p][t] for p in approved)
            prob += pulp.lpSum(x[p][t] for p in approved) <= len(approved) * y[i][t]

    for i in voters:
        prob += z[i][0] == y[i][0]

        for t in range(1, rounds):
            prob += z[i][t] == z[i][t-1] + y[i][t]

    for i in voters:
        prob += lam <= z[i][rounds-1]

    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    winners = []

    for t in T:
        for p in C:
            if pulp.value(x[p][t]) == 1:
                winners.append(p)

    return winners


# -----------------------------
# TEMPORAL BORDA
# -----------------------------

def temporal_borda(candidates, ballots, rounds=10):

    winners = []

    for t in range(rounds):

        scores = {c: 0 for c in candidates}

        for ballot in ballots:
            for rank, c in enumerate(ballot):
                scores[c] += len(candidates) - rank

        winner = max(scores, key=scores.get)
        winners.append(winner)

    return winners


# -----------------------------
# TEMPORAL CHAMBERLIN-COURANT
# -----------------------------

def temporal_cc(candidates, ballots, rounds=10):

    winners = []
    represented = [0]*len(ballots)

    for t in range(rounds):

        best = None
        best_score = -1

        for c in candidates:

            score = 0

            for i, ballot in enumerate(ballots):

                if c in ballot and represented[i] == 0:
                    score += 1

            if score > best_score:
                best_score = score
                best = c

        winners.append(best)

        for i, ballot in enumerate(ballots):
            if best in ballot:
                represented[i] += 1

    return winners


# -----------------------------
# METRICS
# -----------------------------

def compute_metrics(winners, ballots):

    voters = len(ballots)
    satisfaction = [0]*voters

    for w in winners:
        for i, ballot in enumerate(ballots):
            if w in ballot:
                satisfaction[i] += 1

    welfare = sum(satisfaction)
    fairness = min(satisfaction)

    return welfare, fairness


# -----------------------------
# EXPERIMENT RUNNER
# -----------------------------

def run_experiments(folder, rounds=10):

    ilp_welfare = []
    borda_welfare = []
    cc_welfare = []

    ilp_fair = []
    borda_fair = []
    cc_fair = []

    dataset_names = []

    for filename in os.listdir(folder):

        if not filename.endswith(".soc") and not filename.endswith(".soi"):
            continue

        path = os.path.join(folder, filename)

        print("Processing:", filename)

        candidates, ballots = parse_soc_file(path)

        if len(candidates) == 0 or len(ballots) == 0:
            continue

        dataset_names.append(filename)

        ilp_winners = solve_temporal_ilp(candidates, ballots, rounds)
        borda_winners = temporal_borda(candidates, ballots, rounds)
        cc_winners = temporal_cc(candidates, ballots, rounds)

        w, f = compute_metrics(ilp_winners, ballots)
        ilp_welfare.append(w)
        ilp_fair.append(f)

        w, f = compute_metrics(borda_winners, ballots)
        borda_welfare.append(w)
        borda_fair.append(f)

        w, f = compute_metrics(cc_winners, ballots)
        cc_welfare.append(w)
        cc_fair.append(f)

    return dataset_names, ilp_welfare, borda_welfare, cc_welfare, ilp_fair, borda_fair, cc_fair


# -----------------------------
# PLOTTING
# -----------------------------

def plot_results(names, ilp_w, borda_w, cc_w, ilp_f, borda_f, cc_f):

    x = range(len(names))

    # Welfare Graph
    plt.figure()

    plt.plot(x, ilp_w, marker='o', label="ILP")
    plt.plot(x, borda_w, marker='o', label="Borda")
    plt.plot(x, cc_w, marker='o', label="Chamberlin-Courant")

    plt.xlabel("Dataset")
    plt.ylabel("Total Welfare")
    plt.title("Welfare Comparison")
    plt.legend()

    plt.xticks(x, names, rotation=45)

    plt.tight_layout()
    plt.show()


    # Fairness Graph
    plt.figure()

    plt.plot(x, ilp_f, marker='o', label="ILP")
    plt.plot(x, borda_f, marker='o', label="Borda")
    plt.plot(x, cc_f, marker='o', label="Chamberlin-Courant")

    plt.xlabel("Dataset")
    plt.ylabel("Minimum Representation")
    plt.title("Fairness Comparison")
    plt.legend()

    plt.xticks(x, names, rotation=45)

    plt.tight_layout()
    plt.show()


# -----------------------------
# MAIN
# -----------------------------

if __name__ == "__main__":

    folder = "00068_poland_local_elections"

    results = run_experiments(folder)

    plot_results(*results)