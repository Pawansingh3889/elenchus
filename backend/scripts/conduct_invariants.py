"""The engine invariants, loaded from the one place they live: app/conduct/invariants.py.

The app runs them over evaluation runs; this module keeps the three readers that cannot
import the app working unchanged. scripts/eval_report.py runs with scripts/ on its path,
scripts/live_conversation.py runs on plain python3 with no backend virtualenv, and the
replay tests import this name. Loaded by file path rather than as ``app.conduct``, because
importing that package would pull in the database layer these readers do not have.
"""

import importlib.util
import sys
from pathlib import Path

_SOURCE = Path(__file__).resolve().parents[1] / "app" / "conduct" / "invariants.py"
_spec = importlib.util.spec_from_file_location("_conduct_invariants_source", _SOURCE)
if _spec is None or _spec.loader is None:
    raise ImportError(f"cannot load the engine invariants from {_SOURCE}")
_module = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _module
_spec.loader.exec_module(_module)

EXPECTED_FOLLOW_UP_CAP = _module.EXPECTED_FOLLOW_UP_CAP
Check = _module.Check
ALL = _module.ALL
check_all = _module.check_all
place_keeping = _module.place_keeping
follow_up_cap = _module.follow_up_cap
forced_probes_were_asked = _module.forced_probes_were_asked
the_answer_before_the_probe_survived = _module.the_answer_before_the_probe_survived
one_scripted_answer_per_question = _module.one_scripted_answer_per_question
