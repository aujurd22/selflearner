import json
import sys

sys.path.insert(0, "/root/mbn/llm")

import numpy as np  # noqa: E402


def visit_stats():
    d = json.load(open("/root/mbn/llm/selflearner_candidates/../../mbn/llm/selflearner_candidates/world_schedule.json")) if False else None
    # read both dense runs' schedules
    out = {}
    for arm in ("m6b_dense_s1", "m6b_dense_delta_s1"):
        try:
            sched = json.load(open(
                f"/djr82/flyloop_placeholder/{arm}/world_schedule.json"))
        except FileNotFoundError:
            continue
    return out


if __name__ == "__main__":
    print(visit_stats())
