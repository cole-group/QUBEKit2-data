# QUBEKit2Testing

All relevant information and input files for the testing of QUBEKit 2

QUBEKit config files, pdbs and xmls are all in the respective run folder, as per [spreadsheet](https://docs.google.com/spreadsheets/d/1KZ-0dXBqrnCeB0vvlfhA43mnr9Qea1sqMtXZcY3ksnY/edit#gid=0)


Each folder for training and testing contains:
 * Final pdbs and xmls for each molecule.
 * A summary of results from QUBEBench.
 * The output file from ForceBalance (optimise.out).
 * A QUBEKit input file which can be used to generate the same data (.json file).


## Optimising Rfree Parameters

In order to optimise a set of Rfree parameters for a particular training set, ForceBalance requires a forcefield for all molecules in a directory named `forcefield`.

Having run QUBEKit and obtained a set of xmls, simply run the `xml_combiner.py` script in the directory which contains all QUBEKit run directories.
This will generate a `combined.xml` file containing the forcefield for all molecules in the training set. 
Any virtual sites used will be added and atoms will be appropriately named and numbered.
This is the forcefield file required by ForceBalance.

The `xml_combiner.py` script contains logic to show ForceBalance which parameters to optimise.
These are in the Lennard-Jones section of the script, where, for example, epsilon is calculated as follows:

```epsilon={bfree}*({vol}/{vfree})/(128*PARM['{ele}Element/{free}free']**6)*{57.65243631675715}```

Here, the `PARM['{ele}Element/{free}free']` describes which element's Rfree value is being optimised, as outlined in the ForceBalance sub-element of the xml file.
More information on selecting custom parameters to optimise can be found in the ForceBalance documentation.

---

Next, ForceBalance requires a target folder, containing files for each molecule:

* A file containing the molecule coordinates used for gas simulations, such as a pdb file.
* A file containing molecule coordinates of several (500) molecules, to be used in liquid simulations.
* A data file, which shows information such as the simulation temperature, expected empirical results, and weighting if some empirical parameters are more important than others. 

For the targets, simply generate a standard liquid box with the desired number of molecules, and edit a data.csv file to contain the relevant values.

An example is laid out here, with some further example files in the targets folder of this repository:

||||||||
|---|---|---|---|---|---|---|
Global|rho_denom|30|||||
Global|hvap_denom|3
Global|kappa_denom|5
Global|cp_denom|2
Global|eps0_denom|2
Global|use_cvib_intra|FALSE
Global|use_cvib_inter|FALSE
Global|use_cni|FALSE
T|P|MBAR|Rho|Rho_wt|Hvap|Hvap_wt
298.15|1.0 atm|FALSE|787|1|37.8|1


Finally, an optimise.in run file is used to control some fitting parameters, and point ForceBalance to the correct files.

An example optimise.in file is given in this repository. A file for a single molecule optimisation would be as follows:

```
$options
forcefield combined.xml
jobtype newton
trust0 0.3
penalty_type L2
penalty_additive 1.0
print_gradient 1
print_hessian 0
print_parameters 1
error_tolerance 1.0
mintrust 0.1
convergence_gradient 0.001
convergence_objective 0.1
convergence_step 0.005
$end

$target
type Liquid_OpenMM
name mol01
liquid_eq_steps 100000
liquid_md_steps 1000000
liquid_timestep 1.0
liquid_interval 1.0
$end
```

Note the `forcefield` flag points to the `combined.xml` file in the `forcefield` folder, 
and the `name` flag points to any molecules in the `targets` folder. 

With the directory structure now like this:

    - main
        - optimise.in
        - forcefield
            - combined.xml
        - targets
            - mol01
                - data.csv
                - gas.pdb
                - liquid.pdb

ForceBalance can be run with the command:

    ForceBalance optimise.in
