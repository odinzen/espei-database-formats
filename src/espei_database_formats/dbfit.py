"""The ``.dbfit`` format: YAML naming a database and the parameters in it to fit.

The database is any file pycalphad can read, chosen by its extension: ``.dat`` (ChemSage),
``.tdb``, or ``.xtdb`` when pycalphad-xtdb is installed.

    database: MQMQA-tern-tests.dat     # relative to this file
    parameters:
      - symbol: VV0001
        phase: TERN_XS_111
        parameter_type: MQMX
        constituents: [[CU, MG], [VA, VA]]
        additional_mixing_constituent: NI
      - symbol: VV0002
        phase: L_SUBG_2
        parameter_type: MQMX
        constituents: [[CU, NI], [VA, VA]]
        exponents: [0, 1, 0, 0]
        mode: offset
        value: -1000.0
"""
from pathlib import Path

import yaml
from pycalphad import Database
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

from .parameters import parameterize_database


def read_dbfit(dbf, fd):
    spec = yaml.safe_load(fd)
    path = Path(spec["database"])
    if not path.is_absolute():
        name = getattr(fd, "name", None)
        if name is None:
            raise ValueError("a .dbfit read from a string needs an absolute database path")
        path = Path(name).resolve().parent / path
    if path.suffix.lower() == ".dbfit":
        raise ValueError(f"{path} is itself a .dbfit")
    source = Database(str(path))
    # fill the Database pycalphad handed us, the way Database.__deepcopy__ copies one
    for key, value in source.__dict__.items():
        if key == "_parameters":
            dbf._parameters = TinyDB(storage=MemoryStorage)
            dbf._parameters.insert_multiple(value.all())
        else:
            setattr(dbf, key, value)
    parameterize_database(dbf, spec.get("parameters", []))
