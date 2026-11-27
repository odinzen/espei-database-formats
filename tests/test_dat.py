import importlib.resources

import numpy as np
import pytest
from pycalphad import Database, calculate

import espei_database_formats
from espei_database_formats import parameterize_database

TEST_DAT = str(importlib.resources.files("pycalphad.tests.databases") / "MQMQA-tern-tests.dat")
TERNARY = dict(symbol="VV0001", phase="TERN_XS_111", parameter_type="MQMX",
               constituents=[["CU", "MG"], ["VA", "VA"]], additional_mixing_constituent="NI")


def _gm(dbf, phase, parameters=None):
    res = calculate(dbf, ["CU", "MG", "NI", "VA"], phase, T=1500.0, P=101325, N=1, pdens=20,
                    parameters=parameters or {})
    return res.GM.values.ravel()


def test_ternary_term_becomes_a_symbol_at_its_value():
    before = _gm(Database(TEST_DAT), "TERN_XS_111")
    dbf = Database(TEST_DAT)
    assert parameterize_database(dbf, [TERNARY]) == {"VV0001": -10000.0}
    assert _gm(dbf, "TERN_XS_111", {"VV0001": -10000.0}) == pytest.approx(before, rel=1e-12, abs=1e-8)
    assert not _gm(dbf, "TERN_XS_111", {"VV0001": -20000.0}) == pytest.approx(before, rel=1e-6)


def test_offset_keeps_the_function_and_a_wrong_offset_shows():
    spec = dict(symbol="VV0002", phase="L_SUBG_2", parameter_type="MQMX",
                constituents=[["CU", "NI"], ["VA", "VA"]], exponents=[0, 1, 0, 0], mode="offset")
    before = _gm(Database(TEST_DAT), "L_SUBG_2")
    right, wrong = Database(TEST_DAT), Database(TEST_DAT)
    parameterize_database(right, [dict(spec, value=-5000.0)])
    parameterize_database(wrong, [dict(spec, value=-4000.0)])   # 1 kJ off the file's -5000
    assert _gm(right, "L_SUBG_2", {"VV0002": -5000.0}) == pytest.approx(before, rel=1e-12, abs=1e-8)
    assert np.max(np.abs(_gm(wrong, "L_SUBG_2", {"VV0002": -5000.0}) - before)) > 1.0


@pytest.mark.parametrize("spec, message", [
    # three binary terms in this phase differ only by their exponents
    (dict(phase="MULTI_XS_0", constituents=[["CU", "NI"], ["VA", "VA"]]), "matches 3 parameters"),
    (dict(phase="MULTI_XS_0", constituents=[["CU", "NI"], ["VA", "VA"]], exponents=[1, 0, 0, 0]), "start at zero"),
    (dict(phase="TERN_XS_111", constituents=[["CU", "MG"], ["VA", "VA"]], additional_mixing_constituent="CU"),
     "matches 0 parameters"),
])
def test_a_spec_must_select_exactly_one_nonzero_parameter(spec, message):
    with pytest.raises(ValueError, match=message):
        parameterize_database(Database(TEST_DAT), [dict(spec, symbol="VV0003", parameter_type="MQMX")])


def test_dbfit_file_loads_through_pycalphad_and_espei_finds_the_symbols(tmp_path):
    from espei.utils import database_symbols_to_fit
    (tmp_path / "x.dbfit").write_text(
        f"database: {TEST_DAT}\n"
        "parameters:\n"
        "  - {symbol: VV0001, phase: TERN_XS_111, parameter_type: MQMX,\n"
        "     constituents: [[CU, MG], [VA, VA]], additional_mixing_constituent: NI}\n")
    dbf = Database(str(tmp_path / "x.dbfit"))
    assert database_symbols_to_fit(dbf) == ["VV0001"]
    assert _gm(dbf, "TERN_XS_111", {"VV0001": -10000.0}) == pytest.approx(_gm(Database(TEST_DAT), "TERN_XS_111"),
                                                                           rel=1e-12, abs=1e-8)


def test_relative_database_path_is_read_next_to_the_dbfit(tmp_path):
    import shutil
    shutil.copy(TEST_DAT, tmp_path / "db.dat")
    (tmp_path / "x.dbfit").write_text("database: db.dat\n")
    assert "TERN_XS_111" in Database(str(tmp_path / "x.dbfit")).phases
