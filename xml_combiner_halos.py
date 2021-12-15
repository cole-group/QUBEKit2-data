#!/usr/bin/env python3

from collections import namedtuple
import os
from xml.dom.minidom import parseString
import xml.etree.ElementTree as ET

import networkx as nx


"""
Add QUBEKit folders (QUBEKit_name_date_log) to wherever this script is being run from.

Script will:
    * Find all QUBEKit created files
    * Isolate the xml data
    * Isolate the necessary L-J params e.g. volume
    * Construct a new xml containing:
        * Forcefield data from all molecules
        * Params needed for forcebalance
"""

from types import SimpleNamespace


class CustomNamespace(SimpleNamespace):
    """
    Adds iteration and dict-style access of keys, values and items to SimpleNamespace.
    TODO Add get() method? (similar to dict)
    """
    def keys(self):
        for key in self.__dict__:
            yield key

    def values(self):
        for value in self.__dict__.values():
            yield value

    def items(self):
        for key, value in self.__dict__.items():
            yield key, value

    def __iter__(self):
        return self.items()


def extract_charge_data(ddec_version=6):
    """
    From Chargemol output files, extract the necessary parameters for calculation of L-J.

    :returns: 3 CustomNamespaces, ddec_data; dipole_moment_data; and quadrupole_moment_data
    ddec_data used for calculating monopole esp and L-J values (used by both LennardJones and Charges classes)
    dipole_moment_data used for calculating dipole esp
    quadrupole_moment_data used for calculating quadrupole esp
    """

    if ddec_version == 6:
        net_charge_file_name = 'DDEC6_even_tempered_net_atomic_charges.xyz'

    elif ddec_version == 3:
        net_charge_file_name = 'DDEC3_net_atomic_charges.xyz'

    else:
        raise ValueError('Unsupported DDEC version; please use version 3 or 6.')

    if not os.path.exists(net_charge_file_name):
        raise FileNotFoundError(
            'Cannot find the DDEC output file.\nThis could be indicative of several issues.\n'
            'Please check Chargemol is installed in the correct location and that the configs'
            ' point to that location.'
        )

    with open(net_charge_file_name, 'r+') as charge_file:
        lines = charge_file.readlines()

    # Find number of atoms
    atom_total = int(lines[0])

    for pos, row in enumerate(lines):
        # Data marker:
        if 'The following XYZ' in row:
            start_pos = pos + 2
            break
    else:
        raise EOFError(f'Cannot find charge data in {net_charge_file_name}.')

    ddec_data = {}
    dipole_moment_data = {}
    quadrupole_moment_data = {}

    for line in lines[start_pos: start_pos + atom_total]:
        # _s are the xyz coords, then the quadrupole moment tensor eigenvalues
        atom_count, atomic_symbol, _, _, _, charge, x_dipole, y_dipole, z_dipole, _, q_xy, q_xz, q_yz, q_x2_y2, q_3z2_r2, *_ = line.split()
        # File counts from 1 not 0; thereby requiring -1 to get the index
        atom_index = int(atom_count) - 1
        ddec_data[atom_index] = CustomNamespace(
            atomic_symbol=atomic_symbol, charge=float(charge), volume=None, r_aim=None, b_i=None, a_i=None
        )

        dipole_moment_data[atom_index] = CustomNamespace(
            x_dipole=float(x_dipole), y_dipole=float(y_dipole), z_dipole=float(z_dipole)
        )

        quadrupole_moment_data[atom_index] = CustomNamespace(
            q_xy=float(q_xy), q_xz=float(q_xz), q_yz=float(q_yz), q_x2_y2=float(q_x2_y2), q_3z2_r2=float(q_3z2_r2)
        )

    r_cubed_file_name = 'DDEC_atomic_Rcubed_moments.xyz'

    with open(r_cubed_file_name, 'r+') as vol_file:
        lines = vol_file.readlines()

    vols = [float(line.split()[-1]) for line in lines[2:atom_total + 2]]

    for atom_index in ddec_data:
        ddec_data[atom_index].volume = vols[atom_index]

    return ddec_data, dipole_moment_data, quadrupole_moment_data


class ParseXML:

    FreeParams = namedtuple('params', 'vfree bfree rfree')
    elem_dict = {
        'H': FreeParams(7.6, 6.5, 1.64),
        'B': FreeParams(46.7, 99.5, 2.08),
        'C': FreeParams(34.4, 46.6, 2.08),
        'N': FreeParams(25.9, 24.2, 1.72),
        'O': FreeParams(22.1, 15.6, 1.60),
        'F': FreeParams(18.2, 9.5, 1.58),
        'P': FreeParams(84.6, 185, 2.07),
        'S': FreeParams(75.2, 134.0, 2.00),
        'Cl': FreeParams(65.1, 94.6, 1.88),
        'Br': FreeParams(95.7, 162.0, 1.96),
        'Si': FreeParams(101.64, 305, 2.08),
        "I": FreeParams(153.8, 385.0, 2.04),
    }

    def __init__(self):

        try:
            os.remove('combined.xml')
        except FileNotFoundError:
            pass

        self.xmls = dict()
        self.ddec_data = dict()

        self.find_xmls_and_ddec_data()
        self.combine_molecules()

    def find_xmls_and_ddec_data(self):
        for i in range(1, 100):
            mol_name = f"mol{str(i).zfill(2)}"
            for file in os.listdir("."):
                if mol_name in file:
                    self.xmls[mol_name] = ET.parse(f'{file}/final_parameters/{mol_name}.xml')

                    home = os.getcwd()
                    os.chdir(f'{file}/charges/ChargeMol')
                    ddec_data, _, _ = extract_charge_data()
                    os.chdir(home)

                    self.ddec_data[mol_name] = ddec_data
            else:
                break

    @staticmethod
    def increment_str(string, increment):
        """Take any standard string from the xml; if it ends in numbers, increment it."""
        if 'QUBE' in string:
            num = int(string[5:]) + increment
            return f'QUBE_{str(num).zfill(4)}'
        if 'v-site' in string:
            num = int(string[6:]) + increment
            return f'v-site{str(num).zfill(4)}'
        try:
            return str(int(string) + increment)
        except ValueError:
            try:
                num = int(string[1:]) + increment
                return string[:1] + str(num)
            except ValueError:
                num = int(string[2:]) + increment
                return string[:2] + str(num)

    def combine_molecules(self):
        """
        * Create a skeleton xml containing all forcefield info.
        * Loop over all molecule xmls found and insert them into this new file.
        * For the Lennard-Jones section, make the necessary adjustments for FB.
        """

        # Create skeleton structure to add molecules into.
        base = ET.Element('ForceField')
        AtomTypes = ET.SubElement(base, 'AtomTypes')
        Residues = ET.SubElement(base, 'Residues')

        HarmonicBondForce = ET.SubElement(base, 'HarmonicBondForce')
        HarmonicAngleForce = ET.SubElement(base, 'HarmonicAngleForce')
        PeriodicTorsionForce = ET.SubElement(base, 'PeriodicTorsionForce')

        NonbondedForce = ET.SubElement(base, 'NonbondedForce', attrib={
            'coulomb14scale': '0.83333', 'lj14scale': '0.5',
            'combination': 'amber'})

        ForceBalance = ET.SubElement(base, 'ForceBalance')
        # TODO Add all (relevant) elements. Exclude elements if they're not in the test set?
        ET.SubElement(ForceBalance, 'FElement', ffree='1.58', bfree='9.5', vfree='18.2', parameterize='ffree')
        ET.SubElement(ForceBalance, 'ClElement', clfree='1.88', bfree='94.6', vfree='65.1', parameterize='clfree')
        ET.SubElement(ForceBalance, 'BrElement', brfree='1.96', bfree='162.0', vfree='95.7', parameterize='brfree')
        # ET.SubElement(ForceBalance, 'IElement', ifree='2.04', bfree='385.0', vfree='153.8', parameterize='ifree')
        ET.SubElement(ForceBalance, 'SElement', sfree='2.00', bfree='134.0', vfree='75.2', parameterize='sfree')

        # Increase by the number of atoms in each molecule upon addition to the combined xml.
        increment = 0
        raise_by = 0

        for mol_name, xmlclass in self.xmls.items():

            # Used to find polar Hs
            topology = nx.Graph()
            atoms = dict()

            root = xmlclass.getroot()
            if root.tag != 'ForceField':
                raise RuntimeError('Not a proper forcefield file.')

            Residue = ET.SubElement(Residues, 'Residue', name=mol_name)
            for child in root:
                if child.tag == 'AtomTypes':
                    for i, atom in enumerate(child):
                        atoms[str(i)] = atom.get('element')
                        if atom.get('element') is not None:
                            ET.SubElement(AtomTypes, 'Type', attrib={
                                'class': self.increment_str(atom.get('class'), increment),
                                'element': atom.get('element'),
                                'mass': atom.get('mass'),
                                'name': self.increment_str(atom.get('name'), increment),
                            })
                        else:
                            ET.SubElement(AtomTypes, 'Type', attrib={
                                'class': self.increment_str(atom.get('class'), increment),
                                'mass': atom.get('mass'),
                                'name': self.increment_str(atom.get('name'), increment),
                            })
                        ET.SubElement(Residue, 'Atom', attrib={
                            'name': self.increment_str(atom.get('class'), increment),
                            'type': self.increment_str(atom.get('name'), increment),
                        })
                    # Get the final value of i for the number of atoms in the molecule.
                    raise_by = i + 1

                elif child.tag == 'Residues':
                    for residue in child:
                        for atom_or_bond in residue:
                            if atom_or_bond.tag == 'Bond':
                                ET.SubElement(Residue, 'Bond', attrib={
                                    # Don't increment the atom indices for the bonds
                                    'from': atom_or_bond.get('from'),
                                    'to': atom_or_bond.get('to'),
                                })
                                topology.add_node(atom_or_bond.get('from'))
                                topology.add_node(atom_or_bond.get('to'))
                                topology.add_edge(atom_or_bond.get('from'), atom_or_bond.get('to'))
                            elif atom_or_bond.tag == 'VirtualSite':
                                if atom_or_bond.get('wx4') is None:
                                    ET.SubElement(Residue, 'VirtualSite', attrib={
                                        'atom1': atom_or_bond.get('atom1'),
                                        'atom2': atom_or_bond.get('atom2'),
                                        'atom3': atom_or_bond.get('atom3'),
                                        'index': atom_or_bond.get('index'),
                                        'p1': atom_or_bond.get('p1'),
                                        'p2': atom_or_bond.get('p2'),
                                        'p3': atom_or_bond.get('p3'),
                                        'type': 'localCoords',
                                        'wo1': '1.0',
                                        'wo2': '0.0',
                                        'wo3': '0.0',
                                        'wx1': '-1.0',
                                        'wx2': '1.0',
                                        'wx3': '0.0',
                                        'wy1': '-1.0',
                                        'wy2': '0.0',
                                        'wy3': '1.0',
                                    })
                                else:
                                    ET.SubElement(Residue, 'VirtualSite', attrib={
                                        'atom1': atom_or_bond.get('atom1'),
                                        'atom2': atom_or_bond.get('atom2'),
                                        'atom3': atom_or_bond.get('atom3'),
                                        'atom4': atom_or_bond.get('atom4'),
                                        'index': atom_or_bond.get('index'),
                                        'p1': atom_or_bond.get('p1'),
                                        'p2': atom_or_bond.get('p2'),
                                        'p3': atom_or_bond.get('p3'),
                                        'type': 'localCoords',
                                        'wo1': '1.0',
                                        'wo2': '0.0',
                                        'wo3': '0.0',
                                        'wo4': '0.0',
                                        'wx1': '-1.0',
                                        'wx2': '0.33333333',
                                        'wx3': '0.33333333',
                                        'wx4': '0.33333333',
                                        'wy1': '1.0',
                                        'wy2': '-1.0',
                                        'wy3': '0.0',
                                        'wy4': '0.0',
                                    })
                elif child.tag == 'HarmonicBondForce':
                    for force in child:
                        ET.SubElement(HarmonicBondForce, 'Bond', attrib={
                            'class1': self.increment_str(force.get('class1'), increment),
                            'class2': self.increment_str(force.get('class2'), increment),
                            'length': force.get('length'),
                            'k': force.get('k'),
                        })

                elif child.tag == 'HarmonicAngleForce':
                    for force in child:
                        ET.SubElement(HarmonicAngleForce, 'Angle', attrib={
                            'class1': self.increment_str(force.get('class1'), increment),
                            'class2': self.increment_str(force.get('class2'), increment),
                            'class3': self.increment_str(force.get('class3'), increment),
                            'angle': force.get('angle'),
                            'k': force.get('k'),
                        })

                elif child.tag == 'PeriodicTorsionForce':
                    for force in child:
                        ET.SubElement(PeriodicTorsionForce, force.tag, attrib={
                            # TODO Automate attribute access when they're the same?
                            'class1': self.increment_str(force.get('class1'), increment),
                            'class2': self.increment_str(force.get('class2'), increment),
                            'class3': self.increment_str(force.get('class3'), increment),
                            'class4': self.increment_str(force.get('class4'), increment),
                            'k1': force.get('k1'),
                            'k2': force.get('k2'),
                            'k3': force.get('k3'),
                            'k4': force.get('k4'),
                            'periodicity1': force.get('periodicity1'),
                            'periodicity2': force.get('periodicity2'),
                            'periodicity3': force.get('periodicity3'),
                            'periodicity4': force.get('periodicity4'),
                            'phase1': force.get('phase1'),
                            'phase2': force.get('phase2'),
                            'phase3': force.get('phase3'),
                            'phase4': force.get('phase4'),
                        })

                elif child.tag == 'NonbondedForce':
                    for atom_index, force in enumerate(child):
                        if 'v-site' in force.get('type'):
                            ET.SubElement(NonbondedForce, 'Atom', attrib={
                                'charge': force.get('charge'),
                                'sigma': force.get('sigma'),
                                'epsilon': force.get('epsilon'),
                                'type': self.increment_str(force.get('type'), increment),
                            })
                        else:
                            typ = force.get('type').split('_')[1]
                            atomic_symbol = self.ddec_data[mol_name][atom_index].atomic_symbol
                            ele = atomic_symbol
                            free = atomic_symbol.lower()
                            if atoms[typ] == 'H':
                                for bonded in topology.neighbors(typ):
                                    if atoms[bonded] in ['O', 'N', 'S']:
                                        ele = 'X'
                                        free = 'hpol'
                            vol = self.ddec_data[mol_name][atom_index].volume
                            bfree = self.elem_dict[atomic_symbol].bfree
                            vfree = self.elem_dict[atomic_symbol].vfree
                            if free in ['f', 'cl', 'br', 'i', 's']:
                                ET.SubElement(NonbondedForce, 'Atom', attrib={
                                    'charge': force.get('charge'),
                                    'sigma': force.get('sigma'),
                                    'epsilon': force.get('epsilon'),
                                    'type': self.increment_str(force.get('type'), increment),
                                    'volume': f'{vol}',
                                    'bfree': f'{bfree}',
                                    'vfree': f'{vfree}',
                                    'parameter_eval':
                                        f"epsilon=(1.2207*({vol}/{vfree})**0.48856)*{bfree}/(128*PARM['{ele}Element/{free}free']**6)*{57.65243631675715}, "
                                        f"sigma=2**(5/6)*({vol}/{vfree})**(1/3)*PARM['{ele}Element/{free}free']*{0.1}",
                                })
                            else:
                                ET.SubElement(NonbondedForce, 'Atom', attrib={
                                    'charge': force.get('charge'),
                                    'sigma': force.get('sigma'),
                                    'epsilon': force.get('epsilon'),
                                    'type': self.increment_str(force.get('type'), increment),
                                })
            increment += raise_by

        tree = ET.ElementTree(base).getroot()
        messy = ET.tostring(tree, 'utf-8')
        pretty_xml_as_string = parseString(messy).toprettyxml(indent="")

        with open('combined.xml', 'w+') as xml_doc:
            xml_doc.write(pretty_xml_as_string)


if __name__ == '__main__':
    ParseXML()
