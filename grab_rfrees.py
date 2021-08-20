import os


os.chdir('runs/training')

results = dict()
for i in range(1, 18):
    key = str(i).zfill(3)
    try:
        os.chdir(key)
    except FileNotFoundError:
        continue
    if 'optimise.out' in os.listdir('.'):
        with open('optimise.out') as opt_file:
            lines = opt_file.readlines()[20:]
            for j, line in enumerate(lines):
                if 'Final physical parameters:' in line:
                    cfree = float(lines[j + 2].split(' ')[6])
                    nfree = float(lines[j + 3].split(' ')[6])
                    ofree = float(lines[j + 4].split(' ')[6])
                    hfree = float(lines[j + 5].split(' ')[6])
                    xfree = float(lines[j + 6].split(' ')[6])

                    try:
                        alpha = float(lines[j + 7].split(' ')[6])
                        beta = float(lines[j + 8].split(' ')[6])
                        results[key] = [cfree, nfree, ofree, hfree, xfree, alpha, beta]
                    except IndexError:
                        results[key] = [cfree, nfree, ofree, hfree, xfree]
    os.chdir('../')

print('run  cfree  nfree  ofree  hfree  xfree  alpha  beta')
for key, value in results.items():
    print(f'run {key}: {value}')
