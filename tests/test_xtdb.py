import importlib.resources

import pytest
from pycalphad import Database, calculate

import espei_dat  # noqa: F401  (registers .datfit and loads pycalphad-xtdb)

pytest.importorskip("pycalphad_xtdb")
TEST_TDB = str(importlib.resources.files("pycalphad.tests.databases") / "alnipt.tdb")


def _gm_liquid(dbf, elements, parameters=None):
    res = calculate(dbf, elements + ["VA"], "LIQUID", T=1800.0, P=101325, N=1, pdens=50,
                    parameters=parameters or {})
    return res.GM.values.ravel()


def test_datfit_reads_an_xtdb_and_offsets_a_redlich_kister_term(tmp_path):
    Database(TEST_TDB).to_file(str(tmp_path / "alnipt.xtdb"))
    before = _gm_liquid(Database(str(tmp_path / "alnipt.xtdb")), ["AL", "NI"])
    (tmp_path / "x.datfit").write_text(
        "database: alnipt.xtdb\n"
        "parameters:\n"
        "  - {symbol: VV0001, phase: LIQUID, parameter_type: L, order: 0,\n"
        "     constituents: [[AL, NI]], mode: offset, value: 1000.0}\n")
    dbf = Database(str(tmp_path / "x.datfit"))
    assert _gm_liquid(dbf, ["AL", "NI"], {"VV0001": 1000.0}) == pytest.approx(before, rel=1e-12, abs=1e-8)
    assert not _gm_liquid(dbf, ["AL", "NI"], {"VV0001": -9000.0}) == pytest.approx(before, rel=1e-6)


TDB_WITH_VV = """ELEMENT VA VACUUM 0 0 0 !
ELEMENT AL FCC_A1 26.98 0 0 !
ELEMENT FE BCC_A2 55.85 0 0 !
FUNCTION VV0001 298.15 -12000; 6000 N !
PHASE LIQUID % 1 1 !
CONSTITUENT LIQUID :AL,FE: !
PARAMETER G(LIQUID,AL;0) 298.15 0; 6000 N !
PARAMETER G(LIQUID,FE;0) 298.15 0; 6000 N !
PARAMETER L(LIQUID,AL,FE;0) 298.15 VV0001; 6000 N !
"""


def test_xtdb_carries_its_own_fitting_symbol(tmp_path):
    """A VV function written into an XTDB file is what ESPEI fits, with no .datfit at all."""
    from espei.utils import database_symbols_to_fit, unpack_piecewise
    tdb = Database.from_string(TDB_WITH_VV, fmt="tdb")
    tdb.to_file(str(tmp_path / "vv.xtdb"))
    dbf = Database(str(tmp_path / "vv.xtdb"))
    assert database_symbols_to_fit(dbf) == ["VV0001"]
    assert unpack_piecewise(dbf.symbols["VV0001"]) == pytest.approx(-12000.0)
    ref = _gm_liquid(tdb, ["AL", "FE"], {"VV0001": -12000.0})
    assert _gm_liquid(dbf, ["AL", "FE"], {"VV0001": -12000.0}) == pytest.approx(ref, rel=1e-12)
    assert not _gm_liquid(dbf, ["AL", "FE"], {"VV0001": -2000.0}) == pytest.approx(ref, rel=1e-6)
