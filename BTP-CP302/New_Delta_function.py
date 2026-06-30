import os
from itertools import permutations

def compute_schulze_with_history(ballots, candidates, voter_weights, dryspell, lambda_value=1.0):
    n = len(candidates)
    if n == 0:
        return None, [], []

    N = len(ballots)
    
    idx = {c: i for i, c in enumerate(candidates)}
    score = {c: 0 for c in candidates}
    for approved in ballots:
        for c in approved:
            if c in score:
                score[c] += 1

    delta = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                delta[i][j] = 0.0
            else:
                a = candidates[i]
                b = candidates[j]
                score_diff = score[a] - score[b]
                dry_diff = dryspell[i] - dryspell[j]
                delta[i][j] = score_diff + lambda_value * dry_diff

    pref_matrix = [[0.0] * n for _ in range(n)]
    for voter_idx, approved in enumerate(ballots):
        power = voter_weights[voter_idx]
        for i, j in permutations(range(n), 2):
            pref_matrix[i][j] += power * delta[i][j]

    path_strength = [[0.0] * n for _ in range(n)]
    for i, j in permutations(range(n), 2):
        if pref_matrix[i][j] > pref_matrix[j][i]:
            path_strength[i][j] = pref_matrix[i][j]

    for k in range(n):
        for i in range(n):
            for j in range(n):
                if i != j:
                    path_strength[i][j] = max(
                        path_strength[i][j],
                        min(path_strength[i][k], path_strength[k][j])
                    )

    potential_winners = []
    for i in range(n):
        if all(i == j or path_strength[i][j] >= path_strength[j][i] for j in range(n)):
            potential_winners.append(candidates[i])

    if len(potential_winners) > 1:
        best = potential_winners[0]
        best_margin = -float("inf")
        for cand in potential_winners:
            ci = idx[cand]
            margin = max(
                pref_matrix[ci][idx[opponent]] - pref_matrix[idx[opponent]][ci]
                for opponent in candidates if opponent != cand
            )
            if margin > best_margin:
                best = cand
                best_margin = margin
        return best, pref_matrix, path_strength

    if len(potential_winners) == 1:
        return potential_winners[0], pref_matrix, path_strength

    best_by_score = max(candidates, key=lambda c: score[c])
    return best_by_score, pref_matrix, path_strength


def iterative_schulze_with_history(ballots, candidates, rounds=10, lambda_value=1.0, debug=False):
    num_voters = len(ballots)
    if num_voters == 0 or len(candidates) == 0:
        return []

    satisfaction_counts = [0] * num_voters
    voter_weights = [1.0] * num_voters

    dryspell = [0] * len(candidates)

    chosen = []

    for r in range(rounds):
        winner, pref_matrix, path_strength = compute_schulze_with_history(
            ballots, candidates, voter_weights, dryspell, lambda_value=lambda_value
        )

        chosen.append(winner)

        for idx_v, approved in enumerate(ballots):
            if winner in approved:
                satisfaction_counts[idx_v] += 1

        voter_weights = [1.0 / (s + 1) for s in satisfaction_counts]

        for i, c in enumerate(candidates):
            if c == winner:
                dryspell[i] = 0
            else:
                dryspell[i] += 1

        if debug:
            print(f"\nRound {r+1}: Winner={winner}")
            print("Scores (approval counts):", {c: sum(1 for b in ballots if c in b) for c in candidates})
            print("DrySpells:", dryspell)
            print("Voter powers:", [round(p, 4) for p in voter_weights])
            print("Pref matrix (rounded):")
            for row in pref_matrix:
                print([round(x, 4) for x in row])

    return chosen


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
                if len(parts) >= 4:
                    try:
                        num = int(parts[3].replace(":", ""))
                        candidates.add(num)
                    except ValueError:
                        pass
            elif not line.startswith("#"):
                parts = line.split(":")
                if len(parts) == 2:
                    try:
                        order = [int(x.strip()) for x in parts[1].split(",") if x.strip() != ""]
                        ballots.append(set(order))
                    except ValueError:
                        pass

    return sorted(list(candidates)), ballots


def process_all_soc_files(folder, rounds=10, lambda_value=1.0, output_file="output2.txt", debug=False):
    with open(output_file, "w") as out:
        for filename in os.listdir(folder):
            if not (filename.endswith(".soi") or filename.endswith(".soc")):
                continue
            filepath = os.path.join(folder, filename)
            candidates, ballots = parse_soc_file(filepath)

            out.write(f"File: {filename}\n")
            print(f"Processing {filename} ...")

            if len(candidates) == 0 or len(ballots) == 0:
                out.write("No candidates or no ballots found; skipped.\n\n")
                print(f"Skipped {filename}: no candidates or ballots.")
                continue

            winners = iterative_schulze_with_history(
                ballots, candidates, rounds=rounds, lambda_value=lambda_value, debug=debug
            )

            for r, w in enumerate(winners, start=1):
                out.write(f"Round {r} winner: {w}\n")
            out.write("Final sequence of winners: " + " ".join(map(str, winners)) + "\n\n")

            print(f"Done {filename}: {' '.join(map(str, winners))}")

    print(f"All results saved to {output_file}")


if __name__ == "__main__":
    folder = "00068_poland_local_elections" 
    rounds = 10
    lambda_value = 1.0
    output_file = "output2.txt"
    debug = False

    process_all_soc_files(folder, rounds=rounds, lambda_value=lambda_value, output_file=output_file, debug=debug)
