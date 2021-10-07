import os
import shutil
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt

from numpy.polynomial.polynomial import polyfit


def find_xmls():
    xmls = dict()
    for root, dirs, files in os.walk('.', topdown=True):
        for di in dirs:
            if 'mol' in di:
                xmls[di] = ET.parse(f'{di}/{di}.xml')
    return xmls


def charges_from_xmls():
    """
    openff_charges = {
        'mol01': {
            0: 0.4569
            1: -0.7345
        }
    }
    """

    xmls = find_xmls()
    charges = []
    for mol_name, xmlclass in xmls.items():
        root = xmlclass.getroot()
        if root.tag != 'ForceField':
            raise RuntimeError('Not a proper forcefield file.')

        for child in root:
            if child.tag == 'NonbondedForce':
                for force in child:
                    charges.append(float(force.get('charge')))

    return charges


def plot(run_a='001', run_b='015'):

    home = os.getcwd()

    os.chdir(run_a)
    run_a_charges = charges_from_xmls()
    os.chdir(home)
    os.chdir(run_b)
    run_b_charges = charges_from_xmls()
    os.chdir(home)

    assert len(run_a_charges) == len(run_b_charges)

    plt.scatter(run_a_charges, run_b_charges, marker='x', c='black', s=25)
    plt.xlabel(run_a)
    plt.ylabel(run_b)
    plt.plot([-1, 1], [-1, 1], c='black')
    plt.title(f'run{run_a} vs run{run_b}')

    intercept, gradient = polyfit(
        run_a_charges, run_b_charges, 1
    )
    print(run_b, end='  ')
    print(round(gradient, 4))
    # plt.show()
    plt.savefig(f'{run_a}_vs_{run_b}')
    plt.figure().clear()


# def new_plot(run='001'):
#
#     os.chdir('runs/test')
#     home = os.getcwd()
#
#     os.chdir('openff')
#     openff_charges = charges_from_xmls()
#     os.chdir(home)
#     os.chdir(run)
#     other_charges = charges_from_xmls()
#     os.chdir(home)
#
#     assert len(openff_charges) == len(other_charges)
#
#     white_viridis = LinearSegmentedColormap.from_list('white_viridis', [
#         (0, '#ffffff'),
#         (1e-20, '#440053'),
#         (0.2, '#404388'),
#         (0.4, '#2a788e'),
#         (0.6, '#21a784'),
#         (0.8, '#78d151'),
#         (1, '#fde624'),
#     ], N=1000)
#     matplotlib.rcParams['lines.markersize'] = 1
#
#     fig = plt.figure(figsize=(15, 8))
#
#     ax = fig.add_subplot(2, 2, 1, projection='scatter_density')
#     density = ax.scatter_density(openff_charges, other_charges, cmap=white_viridis, vmin=0, vmax=150)
#     fig.colorbar(density, label='density')
#     ax.plot([100_000, 1000_000], [100_000, 1000_000], '--', c='red')
#
#     ax.set_xlabel('parsley')
#     ax.set_ylabel(f'run {run}')
#
#     plt.show()


if __name__ == '__main__':

    os.chdir('runs/training')
    runs = [
        '005', '006', '007', '009', '015'
    ]
    for run in runs:
        plot(run_b=run)
    # os.chdir('runs/training/007')
    # for i in range(1, 16):
    #     mol_name = f'mol{str(i).zfill(2)}'
    #     os.mkdir(mol_name)
    #     shutil.copy(f'007a/{mol_name}.xml', f'{mol_name}/{mol_name}.xml')


# def charges_from_workflow():
#     charges = dict()
#     for root, dirs, files in os.walk('.', topdown=True):
#         for di in dirs:
#             if f'QUBEKit_mol' in di:
#                 mol_name = di.split('_')[1]
#                 charges[mol_name] = dict()
#                 os.chdir(di)
#                 w = WorkFlowResult.parse_file(path="workflow_result.json")
#                 mol = w.current_molecule
#                 for atom in mol.atoms:
#                     charges[mol_name][atom.atom_index] = atom.aim.charge
#     return charges
