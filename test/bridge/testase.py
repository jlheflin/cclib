# -*- coding: utf-8 -*-
#
# Copyright (c) 2023, the cclib development team
#
# This file is part of cclib (http://cclib.github.io) and is distributed under
# the terms of the BSD 3-Clause License.

"""Tests for the cclib2ase bridge in cclib."""

from pathlib import Path

from cclib import ccopen
from cclib.bridge import cclib2ase
from cclib.parser.utils import find_package

import numpy as np

if not find_package("ase"):
    raise ImportError("Must install ase to run this test")

import pytest
from ase import Atoms
from ase.calculators.emt import EMT


class ASETest:
    """Tests for the cclib2ase bridge in cclib."""

    def test_makease_allows_optimization(self):
        """Ensure makease works from direct input."""
        h2 = cclib2ase.makease([[0, 0, 0], [0, 0, 0.7]], [1, 1])

        # Check whether converting back gives the expected data,
        data = cclib2ase.makecclib(h2)
        assert np.allclose(data.atomcoords, [[[0, 0, 0], [0, 0, 0.7]]])
        assert np.allclose(data.atomnos, [1, 1])
        assert np.allclose(data.atommasses, [1.008, 1.008])
        assert np.isclose(data.natom, 2)
        assert np.isclose(data.charge, 0)
        assert np.isclose(data.mult, 1)
        assert np.isclose(data.temperature, 0)

    def test_makecclib_retrieves_optimization(self):
        """Ensure makecclib works with native ASE Atoms objects."""
        h2 = Atoms("H2", positions=[[0, 0, 0], [0, 0, 0.7]])

        # Check whether converting back gives the expected data,
        data = cclib2ase.makecclib(h2)
        assert np.allclose(data.atomcoords, [[[0, 0, 0], [0, 0, 0.7]]])
        assert np.allclose(data.atomnos, [1, 1])
        assert np.allclose(data.atommasses, [1.008, 1.008])
        assert np.isclose(data.natom, 2)
        assert np.isclose(data.charge, 0)
        assert np.isclose(data.mult, 1)
        assert np.isclose(data.temperature, 0)

    def test_makease_works_with_openshells(self):
        """Ensure makease works from parsed data for open-shell molecules."""
        # Make sure we can construct an open shell molecule,
        data = ccopen("data/ORCA/basicORCA4.2/dvb_sp_un.out").parse()

        # Check we have no gradients, as they will be generated by ASE.
        with pytest.raises(AttributeError):
            data.grads

        dvb_sp_un = cclib2ase.makease(
            data.atomcoords[-1],
            data.atomnos,
            data.atomcharges["mulliken"],
            data.atomspins["mulliken"],
            data.atommasses,
        )

        # Check whether converting back gives the expected data.
        ase_data = cclib2ase.makecclib(dvb_sp_un)
        assert np.allclose(ase_data.atomcoords, [data.atomcoords[-1]])
        assert np.allclose(ase_data.atomnos, data.atomnos)
        assert np.allclose(ase_data.atomcharges["mulliken"], data.atomcharges["mulliken"])
        assert np.allclose(ase_data.atomspins["mulliken"], data.atomspins["mulliken"])
        assert np.allclose(ase_data.atommasses, data.atommasses)
        assert np.isclose(ase_data.charge, data.charge)
        assert np.isclose(ase_data.mult, data.mult)
        assert np.isclose(ase_data.natom, len(data.atomnos))
        assert np.isclose(ase_data.temperature, 0)

        # Make sure our object is compatible with ASE API.
        dvb_sp_un.calc = EMT(label="dvb_sp_un")  # not a serious calculator!

        # Converting back should give updated results.
        ase_data = cclib2ase.makecclib(dvb_sp_un)
        assert np.allclose(ase_data.atomcoords, [data.atomcoords[-1]])
        assert np.allclose(ase_data.atomnos, data.atomnos)
        assert np.allclose(ase_data.atommasses, data.atommasses)
        assert np.allclose(ase_data.atomcharges["mulliken"], data.atomcharges["mulliken"])
        assert np.allclose(ase_data.atomspins["mulliken"], data.atomspins["mulliken"])
        assert np.isclose(ase_data.charge, data.charge)
        assert np.isclose(ase_data.mult, data.mult)
        assert np.isclose(ase_data.natom, len(data.atomnos))
        assert np.isclose(ase_data.temperature, 0)

        # Both energies and gradients are from the EMT calculation.
        assert np.allclose(ase_data.scfenergies, [7.016800805424298])
        assert np.shape(ase_data.grads) == (1, ase_data.natom, 3)

    def test_makease_works_with_closedshells(self):
        """Ensure makease works from parsed data for closed-shell molecules."""
        # Make sure we can construct a closed shell molecule.
        data = ccopen("data/ORCA/basicORCA4.2/dvb_ir.out").parse()
        dvb_ir = cclib2ase.makease(
            data.atomcoords[-1],
            data.atomnos,
            data.atomcharges["mulliken"],
            None,  # no atomspins
            data.atommasses,
        )

        # check whether converting back gives the expected data.
        ase_data = cclib2ase.makecclib(dvb_ir)
        assert np.allclose(ase_data.atomcoords, [data.atomcoords[-1]])
        assert np.allclose(ase_data.atomnos, data.atomnos)
        assert np.allclose(ase_data.atomcharges["mulliken"], data.atomcharges["mulliken"])
        assert np.allclose(ase_data.atomspins["mulliken"], 0)
        assert np.allclose(ase_data.atommasses, data.atommasses)
        assert np.isclose(ase_data.charge, data.charge, atol=1e-5)
        assert np.isclose(ase_data.mult, data.mult)
        assert np.isclose(ase_data.natom, len(data.atomnos))
        assert np.isclose(ase_data.temperature, 0)

    def test_write_and_read_trivial_trajectories(self, tmp_path):
        """Ensure write and read trajectory files with single structures."""
        # An open-shell single point calculation.
        data = ccopen("data/ORCA/basicORCA4.2/dvb_sp_un.out").parse()
        cclib2ase.write_trajectory(tmp_path / "dvb_sp_un.traj", data)
        trajdata = cclib2ase.read_trajectory(tmp_path / "dvb_sp_un.traj")

        assert np.allclose(trajdata.atomcoords, data.atomcoords)
        assert np.allclose(trajdata.scfenergies, data.scfenergies)
        # No grads here.

        assert np.allclose(trajdata.atomnos, data.atomnos)
        assert np.allclose(trajdata.atommasses, data.atommasses)
        assert np.allclose(trajdata.natom, data.natom)
        assert np.allclose(trajdata.charge, data.charge)
        assert np.allclose(trajdata.mult, data.mult)
        assert np.allclose(trajdata.moments, data.moments)

        # No temperature here.
        # No freeenergy here.

        assert np.allclose(trajdata.atomcharges["mulliken"], data.atomcharges["mulliken"])
        assert np.allclose(trajdata.atomspins["mulliken"], data.atomspins["mulliken"])

        # A closed-shell single structure frequency calculation.
        data = ccopen("data/ORCA/basicORCA4.2/dvb_ir.out").parse()
        cclib2ase.write_trajectory(Path(tmp_path, "dvb_ir.traj"), data)
        trajdata = cclib2ase.read_trajectory(Path(tmp_path, "dvb_ir.traj"))

        assert np.allclose(trajdata.atomcoords, data.atomcoords)
        assert np.allclose(trajdata.scfenergies, data.scfenergies)
        # No grads here.

        assert np.allclose(trajdata.atomnos, data.atomnos)
        assert np.allclose(trajdata.atommasses, data.atommasses)
        assert np.allclose(trajdata.natom, data.natom)
        assert np.allclose(trajdata.charge, data.charge, atol=1e-5)
        assert np.allclose(trajdata.mult, data.mult)
        assert np.allclose(trajdata.moments, data.moments)
        assert np.allclose(trajdata.freeenergy, data.freeenergy)

        # No temperature here.

        assert np.allclose(trajdata.atomcharges["mulliken"], data.atomcharges["mulliken"])
        # No atomspins here.

    def test_write_and_read_opt_trajectories(self, tmp_path):
        """Ensure write and read trajectory files with optimizations."""
        # Geometry optimization.
        data = ccopen("data/ORCA/basicORCA4.2/dvb_gopt.out").parse()
        cclib2ase.write_trajectory(Path(tmp_path, "dvb_gopt.traj"), data)
        trajdata = cclib2ase.read_trajectory(Path(tmp_path, "dvb_gopt.traj"))

        assert np.allclose(trajdata.atomcoords, data.atomcoords)
        assert np.allclose(trajdata.scfenergies, data.scfenergies)
        assert np.allclose(trajdata.grads, data.grads)

        assert np.allclose(trajdata.atomnos, data.atomnos)
        assert np.allclose(trajdata.atommasses, data.atommasses)
        assert np.allclose(trajdata.natom, data.natom)
        assert np.allclose(trajdata.charge, data.charge)
        assert np.allclose(trajdata.mult, data.mult)
        assert np.allclose(trajdata.moments, data.moments, atol=1e-5)

        # No temperature here.
        # No freeenergy here.

        assert np.allclose(trajdata.atomcharges["mulliken"], data.atomcharges["mulliken"])
        # No atomspins here.

    def test_read_ase_native_trajectory(self):
        """Ensure we can read ASE native trajectory files."""
        trajdata = cclib2ase.read_trajectory("test/bridge/h2o.traj")

        assert np.allclose(len(trajdata.atomcoords), 7)
        assert np.allclose(  # initial structure
            trajdata.atomcoords[0], [[0, 0, 0], [1, 0, 0], [0, 1, 0]]
        )
        assert np.allclose(trajdata.scfenergies[0], -324.61300863874163)
        assert np.allclose(  # final structure
            trajdata.atomcoords[-1],
            [
                [0.06884815, 0.06884815, -0.00000000],
                [1.00852115, -0.07736930, 0.00000000],
                [-0.07736930, 1.00852115, 0.00000000],
            ],
        )
        assert np.allclose(trajdata.scfenergies[-1], -324.9073873170798)

        assert np.allclose(trajdata.atomnos, [8, 1, 1])
        assert np.allclose(trajdata.atommasses, [15.999, 1.008, 1.008])
        assert np.allclose(trajdata.natom, 3)
        assert np.allclose(trajdata.charge, 0)
        assert np.allclose(trajdata.mult, 1)
