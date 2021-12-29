import os
with open("../assets/shuangren.txt", "r") as f:
    lines = f.readlines()
    lines = [l.rstrip() for l in lines]
rc = {"0":"的","1":"地","2":"得"}

for ct, line in enumerate(lines):
    try:
        indices = []
        for idx, c in enumerate(line):
            if c in rc.values(): indices.append(idx)
        if not indices: continue
        n = len(line)
        gt = []
        newline = list(line)
        show = list(line)
        for i in indices:
            show[i] = "【{}】".format(line[i])
            newline[i] = "[MASK]"
        for idx, i in enumerate(indices):
            #print("\n"*50)
            print("\n\n0 的        1 地        2 得")
            print("".join(show))
            chr = input()
            while chr not in rc:
                chr = input()
            gt.append(chr)

        with open("../assets/annotated_dataset.txt", "a") as f:
            f.write("<s>{}</s><de>{}</de>\n".format("".join(newline), "".join([rc[idx] for idx in gt])))
    except KeyboardInterrupt:
        print("interrupted at line ",ct)


