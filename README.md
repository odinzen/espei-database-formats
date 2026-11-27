# espei-database-formats

ESPEI fits the parameters it finds as `V`/`VV` symbols in a database. Some formats have nowhere to
put such a symbol, ChemSage DAT files above all, and with them the MQMQA (modified quasichemical)
liquids of oxide, salt and slag databases. This plugin lets ESPEI fit parameters of any database
pycalphad can read:

- a `.dbfit` file, a few lines of YAML that name a database (ChemSage DAT, TDB, or XTDB) and the
  parameters in it that become fitting symbols, for example an MQMQA ternary term;
- XTDB files read directly, through [pycalphad-xtdb](https://github.com/odinzen/pycalphad-xtdb)
  when installed, with `VV` functions written in the file itself.

ESPEI is not modified. Importing `espei_database_formats` registers the `.dbfit` format with
pycalphad, and `espei-database-formats` is ESPEI's own command line with the formats registered
first.

## Install

```
pip install "espei-database-formats[xtdb] @ git+https://github.com/odinzen/espei-database-formats"
```

Requires Python 3.10 or newer, pycalphad 0.11 and ESPEI 0.9.1 or newer. The `xtdb` extra installs
pycalphad-xtdb; leave it out if you only need DAT and TDB.

## Use

A `.dbfit` file names the database (a relative path is read next to the `.dbfit`) and one entry per
parameter to fit. This one makes the ternary term of pycalphad's MQMQA test database fittable:

```yaml
# tern.dbfit
database: MQMQA-tern-tests.dat
parameters:
  - symbol: VV0001
    phase: TERN_XS_111
    parameter_type: MQMX
    constituents: [[CU, MG], [VA, VA]]
    additional_mixing_constituent: NI
```

Point ESPEI's MCMC at it and run the plugin's command in place of `espei`:

```yaml
# mcmc.yaml
system: {phase_models: phases.json, datasets: datasets}
mcmc: {input_db: tern.dbfit, iterations: 1000, chains_per_parameter: 2, chain_std_deviation: 0.1}
```

```
espei-database-formats --input mcmc.yaml
```

Each entry selects exactly one parameter by `phase`, `parameter_type` and `constituents` (one list
per sublattice; a name matches a species by its name or by its only element), and where needed
`order` (of a Redlich-Kister term), `additional_mixing_constituent` (the third species of an MQMQA
ternary term) and `exponents`. An entry that matches no parameter, or more than one, stops the load
and says how many it matched.

- `mode: replace` (the default) turns a constant parameter into the symbol, starting at its value.
- `mode: offset` with a nonzero `value` keeps a temperature-dependent function and fits a shift of
  its constant part: the parameter becomes `expr - value + symbol`, unchanged at the start.

From Python, `import espei_database_formats` and then `Database("tern.dbfit")`, or call
`parameterize_database(dbf, specs)` on a Database you already hold.

## Tests

```
pip install -e ".[xtdb,test]"
pytest tests
```

About a minute. On pycalphad's own test databases, the tests check:
- that a database gives the same Gibbs energy before and after a parameter becomes a symbol at its
  starting value, and that moving the symbol (or a planted 1 kJ offset error) changes it, for an
  MQMQA ternary term in a DAT file and a Redlich-Kister term in an XTDB file;
- that ESPEI finds a `VV` function written into an XTDB file and reads its starting value;
- that an entry matching zero or several parameters is refused.

## Provenance

Written against the public interfaces of ESPEI and pycalphad (both MIT). ESPEI's source was read to
find where a plugin can hook in (`espei_script.py`, `error_functions/zpf_error.py`, `utils.py`,
`refdata.py`, and how the optimizers read starting values), as were pycalphad's `io/database.py`
and the parameter layout its DAT reader produces. No code was copied from either.

## License and citation

Code: MIT, copyright Odinzen LLC. Data and figures: CC BY 4.0 (this release ships none). If you use
this package, please cite it (see `CITATION.cff`), and
cite ESPEI (Bocklund et al., MRS Communications 9 (2019) 618, doi:10.1557/mrc.2019.59) and pycalphad
(Otis and Liu, Journal of Open Research Software 5 (2017) 1, doi:10.5334/jors.140), which it drives.
