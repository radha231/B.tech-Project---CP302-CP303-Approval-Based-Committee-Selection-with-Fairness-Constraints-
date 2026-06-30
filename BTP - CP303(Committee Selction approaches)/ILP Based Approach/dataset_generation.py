import os
import random
folder = "temporal_datasets"
os.makedirs(folder, exist_ok=True)
num_files = 15
for f in range(1, num_files+1):
    # random sizes for each dataset
    num_rounds = random.randint(6, 12)
    num_voters = random.randint(6, 15)
    num_candidates = random.randint(4, 8)
    candidates = list(range(1, num_candidates+1))
    voters = list(range(1, num_voters+1))
    path = os.path.join(folder, f"dataset{f}.txt")
    with open(path, "w") as file:
        file.write("# candidates\n")
        file.write(" ".join(map(str, candidates)) + "\n\n")
        file.write("# voters\n")
        file.write(" ".join(map(str, voters)) + "\n\n")
        file.write("# rounds\n")
        file.write(str(num_rounds) + "\n\n")
        file.write("# approvals\n\n")

        for r in range(1, num_rounds+1):
            file.write(f"# round {r}\n")
            for v in voters:
                # each voter approves 1–3 candidates
                approved = random.sample(
                    candidates,
                    random.randint(1, min(3, num_candidates))
                )
                approved.sort()
                file.write(f"{v}: {','.join(map(str, approved))}\n")
            file.write("\n")

print("15 dataset files created with varying voters, candidates, and rounds.")

