
#!/usr/bin/env python3
"""
test_utils.py

Pipeline structure checks for TestingTools constants modules.
"""

from importlib import import_module
from modules.display_utils import print_dict_table


# ---------------------------------------------------------------------
# TEST STATUS
# ---------------------------------------------------------------------

def get_test_status(modules: list[str]) -> list[dict]:
    """Return whether each configured constants module can be imported."""
    rows = []
    for name in modules:
        try:
            import_module(f"constants.{name}")
            ready = True
        except Exception as exc:
            print(f"[ERROR] Cannot import {name}: {exc}")
            ready = False
        rows.append({"module": name, "ready": ready})
    return rows


# ---------------------------------------------------------------------
# PIPELINE LOADING
# ---------------------------------------------------------------------


def load_test_pipelines(modules: str | list[str]) -> dict:
    """Load pipeline definitions for the selected constants modules."""
    if isinstance(modules, str):
        modules = [modules]
    pipelines = {}
    for name in modules:
        module = import_module(f"constants.{name}")
        states = getattr(module, "PIPELINE_STATES", None)
        if not isinstance(states, dict):
            raise ValueError(f"{name} has no PIPELINE_STATES dictionary")
        print(f"[OK] Loaded {len(states)} pipelines from constants/{name}.py")
        for state, spec in states.items():
            key = f"{name}.{state}"
            pipelines[key] = spec
    return pipelines


# ---------------------------------------------------------------------
# PIPELINE VALIDATION
# ---------------------------------------------------------------------

def check_pipeline_structure(pipelines: dict) -> bool:
    """Check step functions, phases, arguments, results, and condition dependencies."""
    summary = []
    for name, state in pipelines.items():
        rows = []
        results = set()
        steps = state.get("pipeline") if isinstance(state, dict) else None
        pipeline_ok = isinstance(steps, list) and bool(steps)
        if not pipeline_ok:
            rows.append({
                "Function": "PIPELINE",
                "When": "-",
                "Result": "-",
                "Status": "FAIL",
            })
        else:
            for step in steps:
                config = step if isinstance(step, dict) else {}
                fn = config.get("fn")
                condition = config.get("when")
                result = config.get("result")
                conditions = condition if isinstance(condition, list) else [condition]
                dependency_ok = all(
                    part is None
                    or callable(part)
                    or isinstance(part, (bool, int))
                    or (
                        isinstance(part, str)
                        and any(
                            option.strip() in results
                            or option.strip() in ("job", "meta", "ctx")
                            or option.strip().startswith(("meta.", "ctx."))
                            for option in part.split(" or ")
                        )
                    )
                    for part in conditions
                )
                step_ok = (
                    callable(fn)
                    and config.get("phase") in ("pre", "exec")
                    and isinstance(config.get("args"), list)
                    and isinstance(result, str)
                    and bool(result)
                    and result != "steps"
                    and dependency_ok
                )
                pipeline_ok = pipeline_ok and step_ok
                rows.append({
                    "Function": getattr(fn, "__name__", str(fn)),
                    "When": str(condition) if condition is not None else "-",
                    "Result": result or "-",
                    "Status": "PASS" if step_ok else "FAIL",
                })
                if isinstance(result, str) and result and result != "steps":
                    results.add(result)
        print_dict_table(
            rows,
            ["Function", "When", "Result", "Status"],
            f"{name} Pipeline Validation",
        )
        summary.append({
            "Pipeline": name,
            "Status": "PASS" if pipeline_ok else "FAIL",
        })
    print_dict_table(
        summary,
        ["Pipeline", "Status"],
        "Pipeline Validation Summary",
    )
    passed = sum(item["Status"] == "PASS" for item in summary)
    print(f"[SUMMARY] Passed: {passed}, Failed: {len(summary) - passed}")
    if not summary or passed != len(summary):
        raise ValueError("Pipeline structural validation failed")
    return True
