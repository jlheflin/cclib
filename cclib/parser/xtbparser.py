import re
from datetime import timedelta
from typing import List, Optional, Tuple

from cclib.parser import logfileparser, utils
from cclib.parser.logfilewrapper import FileWrapper

import numpy as np


class XTB(logfileparser.Logfile):
    """An output parser for the xTB code"""

    def __init__(self, *args, **kwargs):
        super().__init__(logname="xTB", *args, **kwargs)

    def __str__(self) -> str:
        """Return a string representation of the object."""
        return f"xTB log file {self.filename}"

    def __repr__(self) -> str:
        """Return a representation of the object."""
        return f'xTB("{self.filename}")'

    def normalisesym(self, label):
        """xTB does not require normalizing symmetry labels."""
        return label

    def before_parsing(self) -> None:
        """Acttions before parsing"""
        pass

    def after_parsing(self) -> None:
        """Actions after parsing"""
        pass

    def _extract_version(self, line: str) -> Optional[str]:
        """
        Extract xtb version from the following:

        -----------------------------------------------------------
        |                   =====================                   |
        |                           x T B                           |
        |                   =====================                   |
        |                         S. Grimme                         |
        |          Mulliken Center for Theoretical Chemistry        |
        |                    University of Bonn                     |
        -----------------------------------------------------------

        * xtb version 6.6.1 (8d0f1dd) compiled by 'conda@1efc2f54142f' on 2023-08-01
        """

        return line.split()[3] if "xtb version" in line else None

    def _extract_coord_file(self, line: str) -> Optional[str]:
        """
        Extract the coordinate filename, from which we can strip out the type

        -------------------------------------------------
        |                Calculation Setup                |
        -------------------------------------------------

        program call               : xtb coord.xyz --opt
        coordinate file            : coord.xyz
        omp threads                :                    20
        """
        return line.split()[-1] if "coordinate file" in line else None

    def _extract_charge(self, line: str) -> Optional[int]:
        """
        Extract the total charge. It can always be found in the
        summary formatted as a float.


         :::::::::::::::::::::::::::::::::::::::::::::::::::::
         ::                     SUMMARY                     ::
         :::::::::::::::::::::::::::::::::::::::::::::::::::::
         :: total energy              -5.070544440612 Eh    ::
         :: gradient norm              0.000057326562 Eh/a0 ::
         :: HOMO-LUMO gap             14.391809984508 eV    ::
         ::.................................................::
         :: SCC energy                -5.104920280363 Eh    ::
         :: -> isotropic ES            0.031458595179 Eh    ::
         :: -> anisotropic ES          0.000396760551 Eh    ::
         :: -> anisotropic XC         -0.000881430881 Eh    ::
         :: -> dispersion             -0.000141085082 Eh    ::
         :: repulsion energy           0.034375839725 Eh    ::
         :: add. restraining           0.000000000000 Eh    ::
         :: total charge              -0.000000000000 e     ::
         :::::::::::::::::::::::::::::::::::::::::::::::::::::
        """
        return round(float(line.split()[-3])) if "total charge" in line else None

    def _extract_final_energy(self, line: str) -> Optional[float]:
        """
        Extract the final total energy from the result table.

           -------------------------------------------------
          | TOTAL ENERGY               -5.070544323569 Eh   |
          | GRADIENT NORM               0.000458081396 Eh/α |
          | HOMO-LUMO GAP              14.381252816459 eV   |
           -------------------------------------------------
        """
        return (
            utils.convertor(float(line.split()[3]), "hartree", "eV")
            if "TOTAL ENERGY" in line
            else None
        )

    def _extract_geom_energy(self, line: str) -> Optional[float]:
        """
                Extract the energies for a geometry step.

        ........................................................................
        .............................. CYCLE    1 ..............................
        ........................................................................

                 iter      E             dE          RMSdq      gap      omega  full diag
                   1     -5.1048382 -0.510484E+01  0.417E-06   14.38       0.0  T
                   2     -5.1048382  0.000000E+00  0.234E-06   14.38   24706.5  T
                   3     -5.1048382  0.000000E+00  0.437E-07   14.38  100000.0  T
                     SCC iter.                  ...        0 min,  0.005 sec
                     gradient                   ...        0 min,  0.010 sec
                 * total energy  :    -5.0705443 Eh     change       -0.4369838E-12 Eh
                   gradient norm :     0.0004582 Eh/α   predicted     0.0000000E+00 (-100.00%)
                   displ. norm   :     0.0005728 α      lambda       -0.1688374E-06
                   maximum displ.:     0.0005029 α      in ANC's #2, #3, #1, ...

                   *** GEOMETRY OPTIMIZATION CONVERGED AFTER 1 ITERATIONS ***
        """

        return (
            utils.convertor(float(line.split()[4]), "hartree", "eV")
            if "* total energy" in line
            else None
        )

    def _extract_symbol_coords(self, line: str, mode: str) -> Optional[Tuple[str, List[float]]]:
        """
        Extract the symbol and X, Y, Z coordinates.

        For XYZ files:

        ================
        final structure:
        ================
        3
        xtb: 6.6.1 (8d0f1dd)
        O            1.07015391331798       -0.01769828395654        0.04981203402603
        H            2.02952514441169       -0.00813780275851        0.03338237327689
        H            0.76845094227033        0.44031608671506       -0.73728440730292

        For SDF/mol files:
        ================
        final structure:
        ================
        energy: -37.337374171651 gnorm: 0.000298918814 xtb: 6.4.0 (d4b70c2)
        xtb     01212213163D
        xtb: 6.4.1 (unknown)
        18 19  0     0  0            999 V2000
          -1.0699    0.0056   -0.3196 C   0  0  0  0  0  0  0  0  0  0  0  0
          -0.1726   -0.9763   -0.3757 O   0  0  0  0  0  0  0  0  0  0  0  0
          -0.4790    1.1791    0.0854 C   0  0  0  0  0  0  0  0  0  0  0  0
        ...
           1.6615    1.5496    0.6104 H   0  0  0  0  0  0  0  0  0  0  0  0
           5.2547   -2.3860    0.3861 H   0  0  0  0  0  0  0  0  0  0  0  0
           3.3873   -4.1943   -0.4469 H   0  0  0  0  0  0  0  0  0  0  0  0
         1  3  2  0  0  0  0
         2  1  1  0  0  0  0
         2  7  1  0  0  0  0
        ...
         14 13  2  0  0  0  0
         15  1  1  0  0  0  0
         18 14  1  0  0  0  0
        M  END
        """
        line_split = line.split()
        if mode == "xyz":
            if line_split[0].isupper():
                return line_split[0], [float(coord) for coord in line_split[1:]]
        elif mode in {"mol", "sdf"}:
            if line_split[3].isupper():
                return line_split[3], [float(coord) for coord in line_split[:3]]
        else:
            raise ValueError(f"Unsupported coordinate file type: {mode}")

    def _extract_orbitals(self, line: str) -> Optional[Tuple[int, float, float, bool]]:
        """
        Extract the orbital index, occupation, energy, and if it's the HOMO.

        * Orbital Energies and Occupations

             #    Occupation            Energy/Eh            Energy/eV
          -------------------------------------------------------------
             1        2.0000           -0.7817342             -21.2721
           ...           ...                  ...                  ...
            21        2.0000           -0.5177364             -14.0883
            22        2.0000           -0.5133906             -13.9701
            23        2.0000           -0.5119411             -13.9306
            24        2.0000           -0.5103339             -13.8869
            25        2.0000           -0.5064217             -13.7804
            26        2.0000           -0.4793904             -13.0449
            27        2.0000           -0.4762317             -12.9589
            28        2.0000           -0.4705819             -12.8052
            29        2.0000           -0.4558376             -12.4040
            30        2.0000           -0.4505134             -12.2591
            31        2.0000           -0.4390552             -11.9473
            32        2.0000           -0.4371482             -11.8954
            33        2.0000           -0.4083272             -11.1111 (HOMO)
            34                         -0.2990289              -8.1370 (LUMO)
            35                         -0.2703399              -7.3563
            36                         -0.2376187              -6.4659
            37                         -0.2246900              -6.1141
            38                         -0.2213822              -6.0241
            39                         -0.2016539              -5.4873
            40                         -0.1317437              -3.5849
            41                         -0.1173862              -3.1942
            42                          0.0207011               0.5633
            43                          0.0378419               1.0297
            44                          0.0843351               2.2949
           ...                                ...                  ...
            60                          1.1799189              32.1072
          -------------------------------------------------------------
                      HL-Gap            0.1092983 Eh            2.9742 eV
                 Fermi-level           -0.3536781 Eh           -9.6241 eV
        """
        line_split = line.split()
        if "(HOMO)" in line or (len(line_split) == 4 and "MO" not in line):
            return (
                int(line_split[0]),
                float(line_split[1]),
                float(line_split[3]),
                bool("(HOMO) in line"),
            )
        if "(LUMO)" in line or (len(line_split) == 3 and "MO" not in line):
            return int(line_split[0]), 0.0, float(line_split[2]), False

    def _extract_gfn2_mulliken_charge(self, line: str) -> Optional[float]:
        """
        Extract Mulliken charge from GFN2-xTB format.

        #   Z          covCN         q      C6AA      α(0)
        1   8 O        1.611    -0.565    24.356     6.661
        2   1 H        0.805     0.282     0.777     1.384
        3   1 H        0.805     0.282     0.777     1.384
        """
        line_split = line.split()
        return float(line_split[4]) if len(line_split) == 7 else None

    def _extract_gfn1_mulliken_cm5_charges(self, line: str) -> Optional[tuple[float, float]]:
        """
        Extract Mulliken and CM5 charge for GFN1-xTB format.

        Mulliken/CM5 charges         n(s)   n(p)   n(d)
            1O    -0.67113 -1.00681   1.689  4.982  0.000
            2H     0.33556  0.50340   0.664  0.000  0.000
            3H     0.33556  0.50340   0.664  0.000  0.000
        """
        line_split = line.split()
        return [float(line_split[1]), float(line_split[2])] if len(line_split) == 6 else None

    def _extract_wall_time(self, line: str) -> Optional[List[timedelta]]:
        """
        Extract the wall time.

         * wall-time:     0 d,  0 h,  0 min,  0.091 sec
        """
        line_split = line.split()
        return (
            [
                timedelta(
                    days=float(line_split[2]),
                    hours=float(line_split[4]),
                    minutes=float(line_split[6]),
                    seconds=float(line_split[8]),
                )
            ]
            if "*" in line and "wall-time" in line
            else None
        )

    def _extract_cpu_time(self, line: str) -> Optional[List[timedelta]]:
        """
        Extract the CPU time.

         *  cpu-time:     0 d,  0 h,  0 min,  1.788 sec
        """
        line_split = line.split()
        return (
            [
                timedelta(
                    days=float(line_split[2]),
                    hours=float(line_split[4]),
                    minutes=float(line_split[6]),
                    seconds=float(line_split[8]),
                )
            ]
            if "*" in line and "cpu-time" in line
            else None
        )

    def _extract_method(self, line: str) -> Optional[str]:
        """
        Extract the method.

        GFN1-xTB:
           -------------------------------------------------
          |                 G F N 1 - x T B                 |
           -------------------------------------------------

        GFN2-xTB:
           -------------------------------------------------
          |                 G F N 2 - x T B                 |
           -------------------------------------------------

        GFN-FF:
           -------------------------------------------------
          |                   G F N - F F                   |
          |          A general generic force-field          |
          |                  Version 1.0.3                  |
           -------------------------------------------------
        """
        return (
            "GFN2-xTB"
            if "G F N 2 - x T B" in line
            else "GFN1-xTB"
            if "G F N 1 - x T B" in line
            else "GFN-FF"
            if "G F N - F F" in line
            else None
        )

    def _extract_multiplicity(self, line: str) -> Optional[int]:
        """
        Extract the spin multiplicity (uhf+1). This is not present
        anywhere in the log file unless the user specifies it via
        a command-line argument. We do the best with what we're given.
        """
        match = re.search(r"(--uhf|-u) (\d+)", line)
        return int(line.split(match.group(2))) + 1 if match else None

    def _extract_symmetry(self, line: str) -> Optional[str]:
        """
        Extract symmetry.

          ...................................................
          :                      SETUP                      :
          :.................................................:
          :  # frequencies                           3      :
          :  # imaginary freq.                       0      :
          :  linear?                             false      :
          :  only rotor calc.                    false      :
          :  symmetry                              c2v      :
        """
        return line.split()[2] if ":" in line and "symmetry" in line else None

    def _extract_enthalpy(self, line: str) -> Optional[float]:
        """
        Extract total enthalpy.

           -------------------------------------------------
          | TOTAL ENERGY               -5.070544323569 Eh   |
          | TOTAL ENTHALPY             -5.046650511691 Eh   |
          | TOTAL FREE ENERGY          -5.068050459618 Eh   |
          | GRADIENT NORM               0.000458233996 Eh/α |
          | HOMO-LUMO GAP              14.381259577706 eV   |
           -------------------------------------------------
        """
        return (
            utils.convertor(line.split()[3], "hartree", "eV") if "TOTAL ENTHALPY" in line else None
        )

    def _extract_entropy(self, line: str) -> Optional[float]:
        """
        Extract total entropy. See summary above.
        """
        return (
            utils.convertor(line.split()[3], "hartree", "eV") if "TOTAL ENTROPY" in line else None
        )

    def _extract_free_energy(self, line: str) -> Optional[float]:
        """
        Extract total free energy. See summary above.
        """
        return (
            utils.convertor(line.split()[4], "hartree", "eV")
            if "TOTAL FREE ENERGY" in line
            else None
        )

    def _extract_zpve(self, line: str) -> Optional[float]:
        """
        Extract ZPVE.

         :::::::::::::::::::::::::::::::::::::::::::::::::::::
         ::                  THERMODYNAMIC                  ::
         :::::::::::::::::::::::::::::::::::::::::::::::::::::
         :: total free energy          -5.068050459618 Eh   ::
         ::.................................................::
         :: total energy               -5.070544323569 Eh   ::
         :: zero point energy           0.020112815395 Eh   ::
         :: G(RRHO) w/o ZPVE           -0.017618951444 Eh   ::
         :: G(RRHO) contrib.            0.002493863951 Eh   ::
         :::::::::::::::::::::::::::::::::::::::::::::::::::::
        """
        return (
            utils.convertor(line.split()[4], "hartree", "eV")
            if "zero point energy" in line
            else None
        )

    def _extract_frequencies(self, line: str) -> Optional[List[float]]:
        """
        Extract the vibrational reduced masses.

                -------------------------------------------------
                |               Frequency Printout                |
                -------------------------------------------------
        projected vibrational frequencies (cm⁻¹)
        eigval :       -0.00    -0.00    -0.00    -0.00    -0.00     0.00
        eigval :     1540.46  3639.49  3648.56
        reduced masses (amu)
        1:  1.86   2:  5.89   3: 14.59   4: 10.55   5: 13.64   6:  1.69   7:  2.15   8:  1.57
        9:  2.11
        IR intensities (km·mol⁻¹)
        1: 66.62   2:134.89   3: 70.64   4: 26.65   5: 33.14   6:142.60   7:133.08   8:  7.15
        9: 16.13
        Raman intensities (amu)
        1:  0.00   2:  0.00   3:  0.00   4:  0.00   5:  0.00   6:  0.00   7:  0.00   8:  0.00
        9:  0.00
        output can be read by thermo (or use thermo option).
        writing <g98.out> molden fake output.
        recommended (thermochemical) frequency scaling factor: 1.0
        """
        match = re.findall(r"[-]?\d+\.\d+", line)
        return [float(val) for val in match] if match else None

    def _extract_reduced_masses(self, line: str) -> Optional[List[float]]:
        """
        Extract the vibrational reduced masses. See summary above.
        """
        match = re.findall(r"\d+\.\d+", line)
        return [float(val) for val in match] if match else None

    def _extract_ir_intensities(self, line: str) -> Optional[List[float]]:
        """
        Extract the vibrational reduced masses. See summary above.
        """
        match = re.findall(r"\d+\.\d+", line)
        return [float(val) for val in match] if match else None

    def _extract_program_call(self, line: str) -> Optional[List[str]]:
        """
        Extract the program call parameters. Note that this won't capture
        the command if the user has supplied it via the xcontrol.

        program call               : xtb coord.xyz --uhf 2 --spinpol --tblite
        """
        return line.split(":")[1].strip().split() if "program call" in line else None

    def _is_geom_cycle_line(self, line: str) -> bool:
        """
        Determine if the line indicates it is a geometry optimization cycle.

        ........................................................................
        .............................. CYCLE    1 ..............................
        ........................................................................
        """

        return "CYCLE" in line

    def _is_geom_end_line(self, line: str) -> bool:
        """
        Determine if the line indicates the optimization is over.

        *** GEOMETRY OPTIMIZATION CONVERGED AFTER 1 ITERATIONS ***

        or

        *** FAILED TO CONVERGE GEOMETRY OPTIMIZATION ***
        """
        return "***" in line and "GEOMETRY OPTIMIZATION" in line

    def _is_success(self, line: str) -> bool:
        """
        Determine if the job finished.

        ------------------------------------------------------------------------
        * finished run on 2023/10/26 at 13:18:28.705
        ------------------------------------------------------------------------
        """
        return "* finished run" in line

    def _is_end_of_structure_block(self, line: str, mode: str) -> bool:
        """
        Determine if the line indicates the end of a structure block.
        Refer to _extract_symbol_coords for examples of structure blocks.
        """
        if mode == "xyz":
            return line == "\n"
        elif mode in {"mol", "sdf"}:
            return "M" in line and "END" in line
        else:
            raise ValueError(f"Unsupported coordinate file type: {mode}")

    def _is_orbitals_line(self, line: str) -> bool:
        """
        Determine if the line indicates the start of a orbital block.

        * Orbital Energies and Occupations

             #    Occupation            Energy/Eh            Energy/eV
          -------------------------------------------------------------
             1        2.0000           -0.7817342             -21.2721
           ...           ...                  ...                  ...
        """
        return "* Orbital Energies and Occupations" in line

    def _is_gfn2_atom_charges(self, line: str) -> bool:
        """
        Determine if there are atom-wise GFN2 charges.

        #   Z          covCN         q      C6AA      α(0)
        """
        return line.split()[:4] == ["#", "Z", "covCN", "q"]

    def _is_gfn1_atom_charges(self, line: str) -> bool:
        """
        Determine if there are atom-wise GFN1 charges.

        Mulliken/CM5 charges         n(s)   n(p)   n(d)
        """
        return "Mulliken/CM5 charges" in line

    def _is_geom_opt_converged(self, line: str) -> bool:
        """
        Determine if the geometry optimization is converged.

        *** GEOMETRY OPTIMIZATION CONVERGED AFTER 1 ITERATIONS ***
        """
        return "***" in line and "GEOMETRY OPTIMIZATION CONVERGED" in line

    def _is_freq_printout(self, line: str) -> bool:
        """
        Determine if we are in the frequency printout.

           -------------------------------------------------
          |               Frequency Printout                |
           -------------------------------------------------
        """
        return "Frequency Printout" in line

    def _is_warning(self, line: str) -> bool:
        """
        Determine if we are in the warning printout.

        ########################################################################
        [WARNING] Runtime exception occurred
        -1- restart_readRestart: Multiplicity missmatch in restart file.
        ########################################################################
        """
        return "[WARNING]" in line

    def extract(self, inputfile: FileWrapper, line: str) -> None:
        if self.metadata.get("success") is None:
            # Initialize as False. Will be overwritten to True if/when appropriate.
            self.metadata["success"] = False

        version = self._extract_version(line)
        if version is not None:
            self.metadata["package_version"] = version

        program_call = self._extract_program_call(line)
        if program_call is not None:
            self.metadata["keywords"] = program_call

        coord_filename = self._extract_coord_file(line)
        if coord_filename is not None:
            self.metadata["coord_type"] = coord_filename.split(".")[-1]

        method = self._extract_method(line)
        if method is not None:
            self.metadata["methods"] = [method]

        charge = self._extract_charge(line)
        if charge is not None:
            self.charge = charge

        mult = self._extract_multiplicity(line)
        if mult is not None:
            self.mult = mult

        # TODO: Use the `xtbopt.xyz` file for SCF energies instead since it has higher precision.
        # But will need to be careful about what might happen if other formats are supplied,
        # such as sdf or POSCAR.
        scf_energies = []
        if self._is_geom_cycle_line(line):
            while not self._is_geom_end_line(line):
                scf_energy = self._extract_geom_energy(line)
                if scf_energy is not None:
                    scf_energies.append(scf_energy)

                line = next(inputfile)

        # TODO: Parse hessian attribute from `hessian` file, if present.

        # TODO: Use the `xtbopt.xyz` file instead since it has higher precision and
        # has the coordinates for every geometry step. If it's not an optimization,
        # can simply assume the structure is the same as that in the coordinate file.
        # But will need to be careful about what might happen if other formats are supplied,
        # such as sdf or POSCAR.
        if "final structure:" in line:
            atomnos = []
            atomcoords = []
            coord_type = self.metadata.get("coord_type")

            while not self._is_end_of_structure_block(line, coord_type):
                symbol_coords = self._extract_symbol_coords(line, coord_type)
                if symbol_coords is not None:
                    symbol, coords = symbol_coords
                    atomnos.append(self.table.number[symbol])
                    atomcoords.append(coords)
                line = next(inputfile)

            if atomnos:
                self.natom = len(atomnos)
                self.atomnos = atomnos
            if atomcoords:
                self.atomcoords = atomcoords

        # TODO: Parse grads attribute from `gradient` file. It will only contain
        # the final gradient, so we'll need to pad it with NaNs to match the
        # number of geometry steps.

        if self._is_orbitals_line(line):
            # Skip 4 lines to get to the table
            next(inputfile)
            next(inputfile)
            next(inputfile)
            line = next(inputfile)

            homos = []
            mooccnos = []
            moenergies = []

            i = 0
            while "------" not in line:
                orbital_info = self._extract_orbitals(line)
                if orbital_info is not None:
                    orbital_idx = orbital_info[0] - 1
                    orbital_occ = orbital_info[1]
                    orbital_energy = orbital_info[2]
                    is_homo = orbital_info[3]

                    # Account for "..." offset
                    offset = orbital_idx - len(moenergies)
                    if offset != 0:
                        moenergies.extend([np.nan] * offset)
                        mooccnos.extend([np.nan] * offset)

                    moenergies.append(orbital_energy)
                    mooccnos.append(orbital_occ)
                    if is_homo:
                        homos.append(orbital_idx)

                i += 1
                line = next(inputfile)

            if moenergies:
                self.moenergies = [np.array(moenergies)]
            if mooccnos:
                self.mooccnos = np.array(mooccnos)
            if homos:
                self.homos = np.array(homos)

        # TODO: Use `charges` file for Mulliken instead since it has higher precision.
        mulliken = []
        cm5 = []
        if self._is_gfn1_atom_charges(line):
            line = next(inputfile)
            while line != "\n":
                charges = self._extract_gfn1_mulliken_cm5_charges(line)
                if charges is not None:
                    mulliken.append(charges[0])
                    cm5.append(charges[1])
                line = next(inputfile)

        if self._is_gfn2_atom_charges(line):
            line = next(inputfile)
            while line != "\n":
                q = self._extract_gfn2_mulliken_charge(line)
                if q is not None:
                    mulliken.append(q)
                line = next(inputfile)

        if mulliken or cm5:
            self.atomcharges = {}
        if mulliken:
            self.atomcharges["mulliken"] = np.array(mulliken)
        if cm5:
            self.atomcharges["cm5"] = np.array(cm5)

        final_energy = self._extract_final_energy(line)
        if final_energy is not None:
            if scf_energies:
                # Patch the final total energy to be the last SCF energy
                # since it is higher precision and also always available
                scf_energies[-1] = final_energy
            else:
                # We only have the final energy to store (e.g. for static)
                scf_energies = [final_energy]

        if scf_energies:
            self.scfenergies = np.array(scf_energies)

        symmetry = self._extract_symmetry(line)
        if symmetry is not None:
            self.metadata["symmetry_detected"] = symmetry
            self.metadata["symmetry_used"] = symmetry

        if self._is_freq_printout(line):
            next(inputfile)
            next(inputfile)
            line = next(inputfile)
            vibfreqs = []
            vibrmasses = []
            vibirs = []

            while "reduced masses" not in line:
                freq_vals = self._extract_frequencies(line)
                if freq_vals is not None:
                    vibfreqs.extend(freq_vals)
                line = next(inputfile)
                if "------" in line:
                    break

            line = next(inputfile)

            while "IR intensities" not in line:
                mass_vals = self._extract_reduced_masses(line)
                if mass_vals is not None:
                    vibrmasses.extend(mass_vals)
                line = next(inputfile)
                if "------" in line:
                    break

            if vibfreqs:
                self.vibfreqs = np.array(vibfreqs)
            if vibrmasses:
                self.vibrmasses = np.array(vibrmasses)
            if vibirs:
                self.vibirs = np.array(vibirs)

        zpve = self._extract_zpve(line)
        if zpve is not None:
            self.zpve = zpve

        entropy = self._extract_entropy(line)
        if entropy is not None:
            self.enthalpy = entropy

        enthalpy = self._extract_enthalpy(line)
        if enthalpy is not None:
            self.enthalpy = enthalpy

        free_energy = self._extract_free_energy(line)
        if free_energy is not None:
            self.freenergy = free_energy

        warnings = []
        if self._is_warning(line):
            while "###" not in line:
                warnings.append(line)
                line = next(inputfile)
        if warnings:
            self.metadata["warnings"] = warnings

        wall_time = self._extract_wall_time(line)
        if wall_time is not None:
            self.metadata["wall_time"] = wall_time

        cpu_time = self._extract_cpu_time(line)
        if cpu_time is not None:
            self.metadata["cpu_time"] = cpu_time

        if self._is_success(line):
            self.metadata["success"] = True
