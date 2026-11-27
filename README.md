# espei-dat

A plugin that lets ESPEI fit parameters of databases whose file format cannot carry ESPEI's
fitting symbols, first of all ChemSage DAT files with an MQMQA (quasichemical) liquid. ESPEI fits
the parameters it finds as `V`/`VV` symbols; a DAT file has nowhere to put one. Importing
`espei_dat` registers a `.datfit` format with pycalphad: a short YAML file that names a database
(DAT, TDB, or XTDB with pycalphad-xtdb) and the parameters in it that become symbols. It also loads
pycalphad-xtdb when installed, so an XTDB file can carry `VV` functions itself. ESPEI is not
modified; `espei-dat` is ESPEI's own command line with the format registered first.

```yaml
# slag.datfit
database: CaO-FeO-MgO-Al2O3-SiO2.dat
parameters:
  - {symbol: VV0001, phase: CAO-FEO-MGO-ALO1.5-SIO2-LIQUID, parameter_type: MQMX,
     constituents: [[CA, AL], [O]], additional_mixing_constituent: MG}
  - {symbol: VV0002, phase: C3MA2, parameter_type: G, constituents: [[AL], [CA], [MG], [O]],
     mode: offset, value: -1220.0}
```

```yaml
# ESPEI input, run with:  espei-dat --input mcmc.yaml
system: {phase_models: phases.json, datasets: datasets}
mcmc: {input_db: slag.datfit, iterations: 1000, chains_per_parameter: 2, chain_std_deviation: 0.1}
```

Each entry selects exactly one parameter (by phase, type, constituents, and optionally `order`,
`additional_mixing_constituent`, `exponents`), or the load fails and says how many matched.
`mode: replace` (default) makes a constant parameter the symbol, starting at its value;
`mode: offset` keeps a temperature-dependent function and fits a shift of its constant part.

## Contents

| Folder | What is in it |
|---|---|
| `src/espei_dat/` | `parameters.py` (parameters to symbols), `datfit.py` (the format), `cli.py` (`espei-dat`) |
| `tests/` | DAT tests on pycalphad's MQMQA test database; XTDB tests (skipped without pycalphad-xtdb) |

## Setup and running

```
pip install -e ".[xtdb,test]"
pytest tests
```

The tests take about a minute. Each checks that the database gives the same Gibbs energy before
and after a parameter becomes a symbol at its starting value, and that moving the symbol (or a
planted 1 kJ offset error) changes it.

## Status

- 2026-11-27: written to fit the CaO-MgO-Al2O3 liquid of Hephaestus's five-oxide slag file with
  ESPEI's MCMC, for parameter uncertainty. pycalphad reproduces that file's liquid (chemical groups
  and ternary terms) to 4e-16 relative and its compounds to round-off, and ESPEI's ZPF error runs
  on it unmodified.
- Next: a first ESPEI run on that system. Possibly offered to the ESPEI project later.
- Private, not released; a license file comes with a public release (MIT).

## Provenance

Written against the public APIs of ESPEI and pycalphad (both MIT). ESPEI's source was read while
writing it (`espei_script.py`, `error_functions/zpf_error.py`, `utils.py`, `refdata.py`, and the
`unpack_piecewise` call in `optimizers`), as were pycalphad's `io/database.py` and the parameter
layout its `io/cs_dat.py` produces, to find where a plugin can hook in. No code was copied from
either. The same function was first written as a patch inside a local ESPEI copy, then moved here
so ESPEI stays unmodified.

## Citation and license

Not yet released. Cite ESPEI and pycalphad for the methods this plugin drives.
