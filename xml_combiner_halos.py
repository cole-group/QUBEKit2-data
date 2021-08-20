#!/usr/bin/env python3

from QUBEKit.utils import constants
# from QUBEKit.utils.file_handling import extract_charge_data

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
        for root, dirs, files in os.walk('.', topdown=True):
            for di in dirs:
                if f'QUBEKit_' in di:
                    mol_name = di.split('_')[1]
                    self.xmls[mol_name] = ET.parse(f'{di}/11_finalise/{mol_name}.xml')

                    home = os.getcwd()
                    os.chdir(f'{di}/08_lennard_jones')
                    ddec_data, _, _ = extract_charge_data()
                    os.chdir(home)

                    self.ddec_data[mol_name] = ddec_data

    @staticmethod
    def increment_str(string, increment):
        """Take any standard string from the xml; if it ends in numbers, increment it."""
        if 'QUBE' in string:
            num = int(string[5:]) + increment
            return f'QUBE_{str(num).zfill(4)}'
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
        # ET.SubElement(ForceBalance, 'CElement', cfree='2.08', bfree='46.6', vfree='34.4', parameterize='cfree')
        # ET.SubElement(ForceBalance, 'NElement', nfree='1.72', bfree='24.2', vfree='25.9', parameterize='nfree')
        # ET.SubElement(ForceBalance, 'OElement', ofree='1.60', bfree='15.6', vfree='22.1', parameterize='ofree')
        # ET.SubElement(ForceBalance, 'HElement', hfree='1.64', bfree='6.5', vfree='7.6', parameterize='hfree')
        # ET.SubElement(ForceBalance, 'XElement', hpolfree='1.00', bfree='6.5', vfree='7.6', parameterize='hpolfree')
        ET.SubElement(ForceBalance, 'FElement', ffree='1.58', bfree='9.5', vfree='18.2', parameterize='ffree')
        ET.SubElement(ForceBalance, 'ClElement', clfree='1.88', bfree='94.6', vfree='65.1', parameterize='clfree')
        ET.SubElement(ForceBalance, 'BrElement', brfree='1.96', bfree='162.0', vfree='95.7', parameterize='brfree')
        ET.SubElement(ForceBalance, 'IElement', ifree='2.04', bfree='385.0', vfree='153.8', parameterize='ifree')
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
                        ET.SubElement(AtomTypes, 'Type', attrib={
                            'class': self.increment_str(atom.get('class'), increment),
                            'element': atom.get('element'),
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
                        if atomic_symbol.lower() in ['f', 'cl', 'br', 'i', 's']:
                            ET.SubElement(NonbondedForce, 'Atom', attrib={
                                'charge': force.get('charge'),
                                'sigma': force.get('sigma'),
                                'epsilon': force.get('epsilon'),
                                'type': self.increment_str(force.get('type'), increment),
                                'volume': f'{vol}',
                                'bfree': f'{bfree}',
                                'vfree': f'{vfree}',
                                'parameter_eval':
                                    f"epsilon={bfree}/(128*PARM['{ele}Element/{free}free']**6)*{constants.EPSILON_CONVERSION}, "
                                    f"sigma=2**(5/6)*({vol}/{vfree})**(1/3)*PARM['{ele}Element/{free}free']*{constants.SIGMA_CONVERSION}",
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
