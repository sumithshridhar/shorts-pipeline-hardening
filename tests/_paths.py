"""Makes the modules in ../pipeline importable from the tests.

The pipeline folder is not a package (it has no __init__.py) because the modules
import each other by bare name (`from niche import ID_PREFIX`). So the tests add the
folder to sys.path instead.
"""

import importlib.util
import os
import sys
from contextlib import contextmanager

PIPELINE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pipeline")
PIPELINE_DIR = os.path.abspath(PIPELINE_DIR)

if PIPELINE_DIR not in sys.path:
    sys.path.insert(0, PIPELINE_DIR)


@contextmanager
def fake_niche_module(module):
    """Temporarily make `import niche` return `module` (or fail if it is None)."""
    missing = object()
    saved = sys.modules.get("niche", missing)
    sys.modules["niche"] = module  # None makes the import raise ImportError
    try:
        yield
    finally:
        if saved is missing:
            sys.modules.pop("niche", None)
        else:
            sys.modules["niche"] = saved


def load_fresh_script_ids():
    """Import a private copy of script_ids.py, so PREFIX is re-read from niche."""
    spec = importlib.util.spec_from_file_location(
        "script_ids_under_test", os.path.join(PIPELINE_DIR, "script_ids.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
