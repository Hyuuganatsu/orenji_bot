# pick examples that have the two rare words to compose a dataset.

import os
baishao = []
with open("../assets/annotated_dataset.txt", "r") as f:
    lines = f.readlines()
count = 0
with open("../assets/picked_dataset.txt", "w") as f:
    for line in lines:
        if "地" in line or "得" in line:
            f.write(line)
            count += 1
        else:
            baishao.append(line)
with open("../assets/picked_dataset.txt", "a") as f:
    f.writelines(baishao[:min(len(baishao), count)])