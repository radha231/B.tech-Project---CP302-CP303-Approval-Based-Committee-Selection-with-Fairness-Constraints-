import os
import pulp
import matplotlib.pyplot as plt

# PARSE TEMPORAL DATASET
def parse_temporal_dataset(filepath):
    candidates = []
    voters = []
    rounds = 0
    approvals = {}
    current_round = None
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("# candidates"):
                candidates = list(map(int, next(f).split()))
            elif line.startswith("# voters"):
                voters = list(map(int, next(f).split()))
            elif line.startswith("# rounds"):
                rounds = int(next(f))
            elif line.startswith("# round"):
                current_round = int(line.split()[2]) - 1
                approvals[current_round] = {}
            elif ":" in line:
                v, app = line.split(":")
                approvals[current_round][int(v)-1] = set(map(int, app.split(",")))

    return candidates, voters, rounds, approvals

# ILP SOLVER (Committee)
def solve_temporal_ilp(candidates, voters, rounds, approvals, k):
    C = candidates
    N = voters
    T = list(range(rounds))
    epsilon = 0.01
    prob = pulp.LpProblem("TemporalVoting", pulp.LpMaximize)
    x = pulp.LpVariable.dicts("x", (C, T), 0, 1, pulp.LpBinary)
    y = pulp.LpVariable.dicts("y", (range(len(N)), T), 0, 1, pulp.LpBinary)
    z = pulp.LpVariable.dicts("z", (range(len(N)), T), 0)
    lam = pulp.LpVariable("lambda", 0)
    prob += pulp.lpSum(y[i][t] for i in range(len(N)) for t in T) + epsilon * lam

    # committee size constraint
    for t in T:
        prob += pulp.lpSum(x[p][t] for p in C) == k

    # representation constraints
    for i in range(len(N)):
        for t in T:
            approved = approvals[t][i]

            prob += y[i][t] <= pulp.lpSum(x[p][t] for p in approved)
            prob += pulp.lpSum(x[p][t] for p in approved) <= len(approved) * y[i][t]

    # cumulative satisfaction
    for i in range(len(N)):
        prob += z[i][0] == y[i][0]

        for t in range(1, rounds):
            prob += z[i][t] == z[i][t-1] + y[i][t]

    for i in range(len(N)):
        prob += lam <= z[i][rounds-1]

    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    committees = []

    for t in T:
        committee = []
        for p in C:
            if pulp.value(x[p][t]) == 1:
                committee.append(p)
        committees.append(committee)

    return committees

# TEMPORAL BORDA (Committee)
def temporal_borda(candidates, voters, rounds, approvals, k):
    committees = []
    for t in range(rounds):
        scores = {c: 0 for c in candidates}
        for i in range(len(voters)):
            ballot = approvals[t][i]
            for c in ballot:
                scores[c] += 1
        committee = sorted(scores, key=scores.get, reverse=True)[:k]
        committees.append(committee)
    return committees

# TEMPORAL CC (Greedy Committee)
def temporal_cc(candidates, voters, rounds, approvals, k):
    committees = []
    for t in range(rounds):
        committee = []
        represented = [0]*len(voters)
        for _ in range(k):
            best = None
            best_score = -1
            for c in candidates:
                if c in committee:
                    continue
                score = 0
                for i in range(len(voters)):
                    if c in approvals[t][i] and represented[i] == 0:
                        score += 1
                if score > best_score:
                    best_score = score
                    best = c
            committee.append(best)
            for i in range(len(voters)):
                if best in approvals[t][i]:
                    represented[i] = 1
        committees.append(committee)
    return committees

# APPROVAL VOTING (Committee)
def temporal_av(candidates, voters, rounds, approvals, k):
    committees = []
    for t in range(rounds):
        scores = {c:0 for c in candidates}
        for i in range(len(voters)):
            for c in approvals[t][i]:
                scores[c] += 1
        committee = sorted(scores, key=scores.get, reverse=True)[:k]
        committees.append(committee)
    return committees

# PROPORTIONAL APPROVAL VOTING
def temporal_pav(candidates, voters, rounds, approvals, k):
    committees = []
    for t in range(rounds):
        committee = []
        represented = [0]*len(voters)
        for _ in range(k):
            best = None
            best_score = -1
            for c in candidates:
                if c in committee:
                    continue
                score = 0
                for i in range(len(voters)):
                    if c in approvals[t][i]:
                        score += 1/(represented[i]+1)
                if score > best_score:
                    best_score = score
                    best = c
            committee.append(best)
            for i in range(len(voters)):
                if best in approvals[t][i]:
                    represented[i] += 1
        committees.append(committee)

    return committees

# METRICS (Committee aware)
def compute_metrics(committees, voters, approvals):
    satisfaction = [0]*len(voters)
    for t, committee in enumerate(committees):
        for i in range(len(voters)):
            if any(c in approvals[t][i] for c in committee):
                satisfaction[i] += 1
    welfare = sum(satisfaction)
    fairness = min(satisfaction)

    return welfare, fairness

# EXPERIMENT RUNNER
def run_experiments(folder, k):
    names = []
    
    ilp_w = []
    borda_w = []
    cc_w = []

    ilp_f = []
    borda_f = []
    cc_f = []

    av_w = []
    pav_w = []

    av_f = []
    pav_f = []
    
    for filename in sorted(os.listdir(folder)):
        if not filename.endswith(".txt"):
            continue
        path = os.path.join(folder, filename)
        candidates, voters, rounds, approvals = parse_temporal_dataset(path)
        print("\nDATASET:", filename)
        ilp = solve_temporal_ilp(candidates, voters, rounds, approvals, k)
        borda = temporal_borda(candidates, voters, rounds, approvals, k)
        cc = temporal_cc(candidates, voters, rounds, approvals, k)
        av = temporal_av(candidates, voters, rounds, approvals, k)
        pav = temporal_pav(candidates, voters, rounds, approvals, k)
        print("ILP Committees:")
        for r, com in enumerate(ilp):
            print("Round", r+1, ":", com)

        w,f = compute_metrics(ilp, voters, approvals)
        ilp_w.append(w)
        ilp_f.append(f)

        w,f = compute_metrics(borda, voters, approvals)
        borda_w.append(w)
        borda_f.append(f)

        w,f = compute_metrics(cc, voters, approvals)
        cc_w.append(w)
        cc_f.append(f)

        w,f = compute_metrics(av, voters, approvals)
        av_w.append(w)
        av_f.append(f)
        
        w,f = compute_metrics(pav, voters, approvals)
        pav_w.append(w)
        pav_f.append(f)
        names.append(filename)

    return names, ilp_w, borda_w, cc_w, av_w, pav_w, ilp_f, borda_f, cc_f, av_f, pav_f

# PLOT RESULTS
def plot_results(names, ilp_w, borda_w, cc_w, av_w, pav_w,
                 ilp_f, borda_f, cc_f, av_f, pav_f):

    x = range(len(names))
    
    # Welfare Graph
    plt.figure()

    plt.plot(x, ilp_w, marker='o', linewidth=3, label="ILP")
    plt.plot(x, borda_w, marker='s', linestyle='--', label="Borda") 
    plt.plot(x, cc_w, marker='^', linestyle=':', label="Chamberlin-Courant")
    plt.plot(x, av_w, marker='d', label="Approval Voting")
    plt.plot(x, pav_w, marker='*', label="PAV")

    all_values = ilp_w + borda_w + cc_w + av_w + pav_w
    plt.ylim(min(all_values) - 5, max(all_values) + 5)

    plt.xticks(x, names, rotation=45)
    plt.ylabel("Welfare")
    plt.title("Welfare Comparison")
    plt.legend()

    plt.tight_layout()
    plt.show()

    plt.figure()
    plt.plot(x, ilp_f, marker='o', label="ILP")
    plt.plot(x, borda_f, marker='s', label="Borda")
    plt.plot(x, cc_f, marker='^', label="Chamberlin-Courant")
    plt.plot(x, av_f, marker='d', label="Approval Voting")
    plt.plot(x, pav_f, marker='*', label="PAV")
    
    plt.xticks(x, names, rotation=45)
    plt.ylabel("Fairness")
    plt.title("Fairness Comparison")
    plt.legend()
    plt.tight_layout()
    plt.show()

# MAIN
folder = "temporal_datasets"
k = 3   # committee size
results = run_experiments(folder, k)
plot_results(*results)
