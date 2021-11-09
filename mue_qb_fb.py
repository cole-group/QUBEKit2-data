import os


def get_dens_hvap_from_qb(file_path='001a_qb_out.txt'):
    """
    Extract the densities and hvaps from the qubebench output.
    :param file_path: qubebench output filepath *a_qb_out.txt
    """

    # Initialise with empty values so order is preserved.
    densities = {i: 0 for i in range(1, 54)}
    enthalpies = {i: 0 for i in range(1, 54)}

    with open(file_path) as qb_file:
        lines = qb_file.readlines()
        for i, line in enumerate(lines):
            if 'Results for:' in line:
                key = int(line[-4:-2])
                dens = float(lines[i+4].split('=')[1])
                hvap = float(lines[i+7].split('=')[1])
                densities[key] = dens
                enthalpies[key] = hvap
    return densities, enthalpies


def get_dens_hvap_from_fb(file_path='optimise.out'):
    """
    Extract the densities and hvaps from the forcebalance output.
    :param file_path: forcebalance output filepath optimise.out
    """

    densities = dict()
    enthalpies = dict()

    with open(file_path) as opt_file:
        lines = opt_file.readlines()
        for i, line in enumerate(lines):
            if 'Density (kg m^-3)' in line:
                key = int(line.split('_')[0][-2:])
                val = float(lines[i + 3].split('+-')[0][-9:].strip()) / 1000

                densities[key] = val

            elif 'Enthalpy of Vaporization (kJ mol^-1)' in line:
                key = int(line.split('_')[0][-2:])
                val = float(lines[i + 3].split('+-')[0][-8:].strip()) / 4.184

                enthalpies[key] = val

    return densities, enthalpies


def get_dens_hvap_from_csv(file_path='results.csv'):
    densities = {i: 0 for i in range(1, 54)}
    enthalpies = {i: 0 for i in range(1, 54)}

    with open(file_path) as csv_file:
        for line in csv_file:
            if 'mol' in line:
                key = int(line[3:5])
                densities[key] = float(line.split(',')[3])
                enthalpies[key] = float(line.split(',')[-1])

    return densities, enthalpies


def calc_mues(qb=False, fb=False, csv=False):
    """
    Calculate the MUEs for the QUBEBench and Forcebalance outputs
    """

    exp_densities = {
        1: 787, 2: 787, 3: 733, 4: 736, 5: 713,
        6: 862, 7: 861, 8: 944, 9: 973, 10: 1022,
        11: 810, 12: 620, 13: 662, 14: 785, 15: 785,
    }
    exp_densities = {key: value / 1000 for key, value in exp_densities.items()}

    exp_enthalpies = {
        1: 37.8, 2: 33.4, 3: 35.8, 4: 27.9, 5: 27.4,
        6: 38.1, 7: 42.4, 8: 46.8, 9: 27.7, 10: 55.8,
        11: 52, 12: 25.2, 13: 23.9, 14: 31.3, 15: 45.5,
    }
    exp_enthalpies = {key: value / 4.184 for key, value in exp_enthalpies.items()}

    results = dict()

    if qb:
        for file in os.listdir('.'):
            if file.endswith('_qb_out.txt'):
                qb_file_path = file
                break
        else:
            raise FileNotFoundError('Cannot find qb output file.')

        qb_densities, qb_enthalpies = get_dens_hvap_from_qb(qb_file_path)

        qb_dens_avg_mue = sum(abs(dens - exp_dens) for dens, exp_dens in zip(qb_densities.values(), exp_densities.values())) / 15
        qb_hvap_avg_mue = sum(abs(hvap - exp_hvap) for hvap, exp_hvap in zip(qb_enthalpies.values(), exp_enthalpies.values())) / 15

        results['qb'] = [round(qb_dens_avg_mue, 4), round(qb_hvap_avg_mue, 4)]

    if csv:
        csv_densities, csv_enthalpies = get_dens_hvap_from_csv()

        print(csv_densities)
        print(exp_densities)

        print(csv_enthalpies)
        print(exp_enthalpies)

        csv_dens_avg_mue = sum(abs(dens - exp_dens) for dens, exp_dens in zip(csv_densities.values(), exp_densities.values())) / 15
        csv_hvap_avg_mue = sum(abs(hvap - exp_hvap) for hvap, exp_hvap in zip(csv_enthalpies.values(), exp_enthalpies.values())) / 15

        results['qb'] = [round(csv_dens_avg_mue, 4), round(csv_hvap_avg_mue, 4)]

    if fb:
        fb_densities, fb_enthalpies = get_dens_hvap_from_fb()

        fb_dens_avg_mue = sum(abs(dens - exp_dens) for dens, exp_dens in zip(fb_densities.values(), exp_densities.values())) / 15
        fb_hvap_avg_mue = sum(abs(hvap - exp_hvap) for hvap, exp_hvap in zip(fb_enthalpies.values(), exp_enthalpies.values())) / 15

        results['fb'] = [round(fb_dens_avg_mue, 4), round(fb_hvap_avg_mue, 4)]

    return results


if __name__ == '__main__':
    # import collections
    # os.chdir('runs/test/014')
    # print(calc_mues(qb=True))
    # dens, hvap = get_dens_hvap_from_qb("014a_qb_out.txt")
    # od = collections.OrderedDict(sorted(dens.items()))
    # for key, val in od.items():
    #     print(val)

    os.chdir('runs/training/011')
    print(calc_mues(fb=True))



    # with open('Q2_testset.csv') as inf, open('Q2_testset_001.csv', 'w+') as outf:
    #     for line in inf:
    #         if '009.ini' in line:
    #             outf.write(line.replace('009.ini', '001.ini'))
    #         else:
    #             outf.write(line)

    # dens = dict()
    # hvap = dict()
    # with open('results.csv') as results:
    #     lines = results.readlines()[1:]
    #     for line in lines:
    #         linelst = line.split(',')
    #         key = linelst[0]
    #         dens[key] = linelst[3]
    #         hvap[key] = linelst[]


    # with open('Q2_testset.csv') as testset:
    #     for line in testset:
    #         print(line.split(',')[4])

# os.chdir('runs')
# for i in range(1, 17):
#     name = str(i).zfill(3)
#     try:
#         os.chdir(name)
#     except FileNotFoundError:
#         continue
#     with open('../../Q2_testset.csv') as in_file, open(f'Q2_testset_{name}.csv', 'w') as out_file:
#         for line in in_file:
#             if 'smiles' in line:
#                 out_file.write(line)
#             else:
#                 out_file.write('mol')
#                 out_file.write(line[:5])
#                 out_file.write(f'{name}.ini')
#                 out_file.write(line[5:])
#     os.chdir('../')
