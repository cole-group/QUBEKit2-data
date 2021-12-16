import os


def get_dens_hvap_from_qb():
    """
    Extract the densities and hvaps from the qubebench output.
    """

    for file in os.listdir('.'):
        if file.endswith('_qb_out.txt'):
            qb_file_path = file
            break
    else:
        raise FileNotFoundError('Cannot find qb output file.')

    # Initialise with empty values so order is preserved.
    densities = {i: 0 for i in range(1, 54)}
    enthalpies = {i: 0 for i in range(1, 54)}

    with open(qb_file_path) as qb_file:
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


def calc_mues(run_type='qb', halos=False):
    """
    Calculate the MUEs for the QUBEBench and Forcebalance outputs
    """

    if halos:
        exp_densities = {
            1: 1096, 2: 831, 3: 707.47, 4: 1182.86, 5: 867.47,
            6: 1153, 7: 1345.5, 8: 1209.52, 11: 1282.14,
            12: 1989.90,
        }
        exp_enthalpies = {
            1: 52.9, 2: 28.41, 3: 20.7, 4: 19.2, 5: 31.5,
            6: 36.2, 7: 31.9, 8: 37.15, 11: 21.9, 12: 17.5,
        }
    else:
        exp_densities = {
            1: 787, 2: 787, 3: 733, 4: 736, 5: 713,
            6: 862, 7: 861, 8: 944, 9: 973, 10: 1022,
            11: 810, 12: 620, 13: 662, 14: 785, 15: 785,
        }
        exp_enthalpies = {
            1: 37.8, 2: 33.4, 3: 35.8, 4: 27.9, 5: 27.4,
            6: 38.1, 7: 42.4, 8: 46.8, 9: 27.7, 10: 55.8,
            11: 52, 12: 25.2, 13: 23.9, 14: 31.3, 15: 45.5,
        }
    exp_densities = {key: value / 1000 for key, value in exp_densities.items()}
    exp_enthalpies = {key: value / 4.184 for key, value in exp_enthalpies.items()}

    densities, enthalpies = {
        'qb': get_dens_hvap_from_qb,
        'fb': get_dens_hvap_from_fb,
        'csv': get_dens_hvap_from_csv,
    }.get(run_type)()

    dens_avg_mue = sum(abs(dens - exp_dens) for dens, exp_dens in zip(densities.values(), exp_densities.values())) / len(exp_densities)
    hvap_avg_mue = sum(abs(hvap - exp_hvap) for hvap, exp_hvap in zip(enthalpies.values(), exp_enthalpies.values())) / len(exp_enthalpies)

    print(f'Density, Hvap MUEs: {round(dens_avg_mue, 4)}, {round(hvap_avg_mue, 4)}')


if __name__ == '__main__':

    os.chdir('../runs/training/019')
    calc_mues('qb', halos=False)
