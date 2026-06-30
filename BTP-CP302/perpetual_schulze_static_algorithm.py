def schulze_round_approval(voters, candidates, weights):
    n = len(candidates)
    index = {c: i for i, c in enumerate(candidates)}

    d = [[0] * n for _ in range(n)]
    for v_idx, approval in enumerate(voters):
        w = weights[v_idx]
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                ci, cj = candidates[i], candidates[j]
                if ci in approval and cj not in approval:
                    d[i][j] += w
                elif ci in approval and cj in approval:
                    d[i][j] += w * 0.5


    p = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j and d[i][j] > d[j][i]:
                p[i][j] = d[i][j]

    for i in range(n):
        for j in range(n):
            if i != j:
                for k in range(n):
                    if i != k and j != k:
                        p[j][k] = max(p[j][k], min(p[j][i], p[i][k]))

    winners = []
    for i in range(n):
        better = True
        for j in range(n):
            if i != j and p[i][j] < p[j][i]:
                better = False
                break
        if better:
            winners.append(candidates[i])

    return winners[0], d, p


def perpetual_schulze_approval(voters, candidates, rounds=3):
    n_voters = len(voters)
    satisfactions = [0] * n_voters
    weights = [1.0] * n_voters
    winners_seq = []

    for r in range(rounds):
        winner, d, p = schulze_round_approval(voters, candidates, weights)
        winners_seq.append(winner)

    
        for v_idx, approval in enumerate(voters):
            if winner in approval:
                satisfactions[v_idx] += 1

    
        weights = [1.0 / (sat + 1) for sat in satisfactions]

        print(f"\nRound {r+1}")
        print("Pairwise matrix d:")
        for row in d:
            print([round(x, 2) for x in row])
        print("Winner:", winner)
        print("Weights:", [round(w, 2) for w in weights])

    return winners_seq


candidates = ["A", "B", "C"]
voters = [
    {"A", "B"},       
    {"B"},       
    {"A", "C"},   
]

winner_seq = perpetual_schulze_approval(voters, candidates, rounds=10)
print("\nWinner sequence:", winner_seq)
