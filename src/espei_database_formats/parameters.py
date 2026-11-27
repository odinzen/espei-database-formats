import logging
from typing import Dict

from pycalphad import Database

_log = logging.getLogger(__name__)


def _species_matches(species, name):
    """True if ``name`` is the species' name or its only element (``"CA"`` matches ``CA+2``)."""
    name = name.upper()
    if species.name is not None and species.name.upper() == name:
        return True
    return set(el.upper() for el in species.constituents) == {name}


def _constituents_match(constituent_array, wanted):
    if len(constituent_array) != len(wanted):
        return False
    for subl, names in zip(constituent_array, wanted):
        if len(subl) != len(names):
            return False
        remaining = list(subl)
        for name in names:
            hit = next((sp for sp in remaining if _species_matches(sp, name)), None)
            if hit is None:
                return False
            remaining.remove(hit)
    return True


def _matches(row, spec):
    if not _constituents_match(row["constituent_array"], spec["constituents"]):
        return False
    if "additional_mixing_constituent" in spec:
        extra = row.get("additional_mixing_constituent")
        if extra is None or not extra.constituents or not _species_matches(extra, spec["additional_mixing_constituent"]):
            return False
    if "exponents" in spec and list(row.get("exponents", [])) != list(spec["exponents"]):
        return False
    if "order" in spec and row.get("parameter_order") != spec["order"]:
        return False
    return True


def parameterize_database(dbf: Database, specs) -> Dict[str, float]:
    """Replace parameters of a loaded Database with fitting symbols, in place.

    Each spec selects exactly one parameter by ``phase``, ``parameter_type`` and ``constituents``
    (one list per sublattice; a name matches a species by its name or by its only element),
    optionally ``order`` (of a Redlich-Kister term), ``additional_mixing_constituent`` (the third
    species of an MQMQA ternary term) and ``exponents``.

    With ``mode: replace`` (the default) the parameter, which must be a constant, becomes the
    ``symbol`` and the symbol starts at its value. With ``mode: offset`` the parameter becomes
    ``expr - value + symbol`` and the symbol starts at ``value``, so the function is unchanged at
    the start and the fit moves its constant part by ``symbol - value``. That suits temperature
    dependent parameters; ``value`` is any nonzero start, ideally of the size of the change.

    Returns the symbols added, mapped to their starting values.
    """
    from symengine import Symbol, sympify
    from tinydb import where
    added = {}
    for spec in specs:
        sym = spec["symbol"]
        if sym in dbf.symbols or sym in added:
            raise ValueError(f"symbol {sym} is already defined")
        query = (where("phase_name") == spec["phase"].upper()) & (where("parameter_type") == spec["parameter_type"])
        rows = [r for r in dbf._parameters.search(query) if _matches(r, spec)]
        if len(rows) != 1:
            raise ValueError(f"spec for {sym} matches {len(rows)} parameters, not 1: {spec}")
        row = rows[0]
        expr = sympify(row["parameter"])
        mode = spec.get("mode", "replace")
        if mode == "replace":
            if expr.free_symbols:
                raise ValueError(f"parameter for {sym} depends on {sorted(map(str, expr.free_symbols))}; "
                                 "use mode: offset")
            value = float(expr)
            new = Symbol(sym)
        elif mode == "offset":
            value = float(spec["value"])
            new = expr - value + Symbol(sym)
        else:
            raise ValueError(f"unknown mode {mode!r} for {sym}")
        if value == 0.0:
            # ESPEI starts its walkers at value * (1 + chain_std_deviation * N(0, 1)), which stays 0
            raise ValueError(f"{sym} would start at zero, where ESPEI's walkers cannot spread")
        dbf._parameters.update({"parameter": new}, doc_ids=[row.doc_id])
        dbf.symbols[sym] = sympify(value)
        added[sym] = value
        _log.info("%s: %s %s %s, start %s", sym, spec["phase"], spec["parameter_type"], spec["constituents"], value)
    return added
