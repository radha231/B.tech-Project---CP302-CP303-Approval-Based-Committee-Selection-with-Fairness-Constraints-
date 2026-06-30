import random
from collections import defaultdict
import statistics as stats

def generate_synthetic_instance(
    m=50,                    # number of candidates
    n=200,                   # number of voters
    d=3,                     # number of attribute dimensions
    attr_sizes=None,         # size of each attribute domain A_j
    p_approve=0.1,           # approval probability
    num_attrs_per_candidate=(2, 3),  # attributes per candidate (for compatibility)
    lambda_coord=1.0,        # λ in Score(S) = U_approval(S) + λ * Coord(S)
    compat_mode='similarity',# 'similarity' or 'conflict'
    conflict_edge_prob=0.02, # for conflict-based compatibility
    seed=None
):
    if seed is not None:
        random.seed(seed)
    if attr_sizes is None:
        attr_sizes = [3] * d

    A = [[f"a{j}_{x}" for x in range(attr_sizes[j])] for j in range(d)]
    candidates = list(range(m))
    attrs = {}
    attr_sets = {}
    for c in candidates:
        vec = []
        aset = set()
        for j in range(d):
            val = random.choice(A[j])
            vec.append(val)
            aset.add(val)
        target = random.randint(num_attrs_per_candidate[0], num_attrs_per_candidate[1])
        all_vals = [v for dom in A for v in dom]
        while len(aset) < target:
            aset.add(random.choice(all_vals))
        attrs[c] = vec
        attr_sets[c] = aset
    voters = list(range(n))
    approvals = {v: set() for v in voters}
    for v in voters:
        for c in candidates:
            if random.random() < p_approve:
                approvals[v].add(c)
    f = {}
    if compat_mode == 'similarity':
        for i in candidates:
            for j in range(i+1, m):
                val = len(attr_sets[i] & attr_sets[j])
                if val != 0:
                    f[(i, j)] = val
    elif compat_mode == 'conflict':
        for i in candidates:
            for j in range(i+1, m):
                if random.random() < conflict_edge_prob:
                    f[(i, j)] = -1
    else:
        raise ValueError("unknown compat_mode")
    diversity_bounds = {}
    for dom in A:
        for val in dom:
            diversity_bounds[val] = (0, m)
    instance = {
        "m": m,
        "n": n,
        "d": d,
        "A": A,
        "candidates": candidates,
        "attrs": attrs,
        "attr_sets": attr_sets,
        "voters": voters,
        "approvals": approvals,
        "f": f,
        "lambda_coord": lambda_coord,
        "diversity_bounds": diversity_bounds,
    }
    return instance

def rep_AV(S, approvals):
    return sum(len(approvals[v] & S) for v in approvals)

def coord_score(S, f):
    S_list = sorted(S)
    total = 0
    for i in range(len(S_list)):
        for j in range(i+1, len(S_list)):
            a, b = S_list[i], S_list[j]
            key = (a, b) if a < b else (b, a)
            total += f.get(key, 0)
    return total

def total_score(S, approvals, f, lambda_coord):
    return rep_AV(S, approvals) + lambda_coord * coord_score(S, f)

def feasible_with_diversity(S, attrs, diversity_bounds):
    counts = defaultdict(int)
    for c in S:
        vec = attrs[c]
        for val in vec:
            counts[val] += 1
    for val, (L, U) in diversity_bounds.items():
        if counts[val] < L or counts[val] > U:
            return False
    return True

def greedy_coordinated(instance, k):
    C = set(instance["candidates"])
    attrs = instance["attrs"]
    approvals = instance["approvals"]
    f = instance["f"]
    lambda_coord = instance["lambda_coord"]
    diversity_bounds = instance["diversity_bounds"]
    S = set()
    while len(S) < k:
        best_c = None
        best_gain = float("-inf")
        base_rep = rep_AV(S, approvals)
        base_coord = coord_score(S, f)
        base_val = base_rep + lambda_coord * base_coord
        for c in C - S:
            S_new = S | {c}
            if not feasible_with_diversity(S_new, attrs, diversity_bounds):
                continue
            val_new = total_score(S_new, approvals, f, lambda_coord)
            gain = val_new - base_val
            if gain > best_gain:
                best_gain = gain
                best_c = c
        if best_c is None:
            break
        S.add(best_c)

    return S

def greedy_AV_only(instance, k):
    C = set(instance["candidates"])
    attrs = instance["attrs"]
    approvals = instance["approvals"]
    diversity_bounds = instance["diversity_bounds"]
    S = set()
    while len(S) < k:
        best_c = None
        best_gain = float("-inf")
        base_rep = rep_AV(S, approvals)
        for c in C - S:
            S_new = S | {c}
            if not feasible_with_diversity(S_new, attrs, diversity_bounds):
                continue
            rep_new = rep_AV(S_new, approvals)
            gain = rep_new - base_rep
            if gain > best_gain:
                best_gain = gain
                best_c = c
        if best_c is None:
            break
        S.add(best_c)
    return S

def random_feasible_committee(instance, k, max_tries=1000):
    C = list(instance["candidates"])
    attrs = instance["attrs"]
    diversity_bounds = instance["diversity_bounds"]
    for _ in range(max_tries):
        S = set(random.sample(C, k))
        if feasible_with_diversity(S, attrs, diversity_bounds):
            return S
    return set()

def run_experiments(
    num_instances=20,
    m=50,
    n=200,
    k=10,
    d=3,
    attr_sizes=None,
    lambda_values=(0.0, 0.5, 1.0, 2.0),
    compat_mode="similarity",
    seed_base=0
):
    if attr_sizes is None:
        attr_sizes = [3] * d
    for lam in lambda_values:
        rep_gc, coord_gc, score_gc = [], [], []
        rep_gav, coord_gav, score_gav = [], [], []
        rep_rand, coord_rand, score_rand = [], [], []
        print(f"\n=== Lambda = {lam} ===")
        for t in range(num_instances):
            inst = generate_synthetic_instance(
                m=m,
                n=n,
                d=d,
                attr_sizes=attr_sizes,
                p_approve=0.1,
                num_attrs_per_candidate=(2, 3),
                lambda_coord=lam,
                compat_mode=compat_mode,
                conflict_edge_prob=0.02,
                seed=seed_base + t
            )
            approvals = inst["approvals"]
            f = inst["f"]
            S_gc = greedy_coordinated(inst, k)
            rep_gc.append(rep_AV(S_gc, approvals))
            coord_gc.append(coord_score(S_gc, f))
            score_gc.append(total_score(S_gc, approvals, f, lam))
            
            S_gav = greedy_AV_only(inst, k)
            rep_gav.append(rep_AV(S_gav, approvals))
            coord_gav.append(coord_score(S_gav, f))
            score_gav.append(total_score(S_gav, approvals, f, lam))
            
            S_rand = random_feasible_committee(inst, k)
            rep_rand.append(rep_AV(S_rand, approvals))
            coord_rand.append(coord_score(S_rand, f))
            score_rand.append(total_score(S_rand, approvals, f, lam))
        def summarize(name, rep_list, coord_list, score_list):
            print(
                f"{name:8s} | "
                f"rep = {stats.mean(rep_list):6.2f}, "
                f"coord = {stats.mean(coord_list):6.2f}, "
                f"score = {stats.mean(score_list):6.2f}"
            )
        summarize("GreedyC", rep_gc, coord_gc, score_gc)
        summarize("GreedyAV", rep_gav, coord_gav, score_gav)
        summarize("Random", rep_rand, coord_rand, score_rand)

# Example: m=50 candidates, n=200 voters, committee size k=10
# similarity-based compatibility, λ in {0,0.5,1,2}
run_experiments(
    num_instances=20,
    m=50,
    n=200,
    k=10,
    d=3,
    attr_sizes=[3, 3, 3],
    lambda_values=(0.0, 0.5, 1.0, 2.0),
    compat_mode="similarity",
    seed_base=1
)
