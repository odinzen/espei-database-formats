"""ESPEI fitting for databases whose format cannot carry ESPEI's fitting symbols.

ESPEI fits parameters it finds as ``V``/``VV`` symbols in the database. Importing this package
registers a ``.datfit`` format with pycalphad: a short YAML file that names a database (ChemSage
DAT, TDB, or XTDB) and the parameters in it that become fitting symbols. It also loads
pycalphad-xtdb when installed, so ESPEI reads ``.xtdb`` files, whose functions can carry the
symbols themselves. Point ESPEI's ``mcmc.input_db`` at either and run ``espei-dat`` in place of
``espei``.
"""
from pycalphad import Database

from .parameters import parameterize_database
from .datfit import read_datfit

try:
    import pycalphad_xtdb  # noqa: F401  (registers .xtdb with pycalphad)
except ImportError:
    pass

__all__ = ["parameterize_database", "read_datfit"]

Database.register_format("datfit", read=read_datfit, write=None)
