"""Golden evaluation fixture checks."""

import json
from pathlib import Path

from packages.postrec_core.domain.run_mode import RunMode
from packages.postrec_core.scoring.verified_ranking import compute_verified_final_score
from packages.postrec_core.validation.recommendation_validator import validate_recommendation

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "golden_eval_topics.json"


def test_golden_eval_good_beats_weak():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    topic = payload["topics"][0]
    papers = topic["papers"]

    good = validate_recommendation(topic["good_proposal"], papers, mode=RunMode.SOTA)
    weak = validate_recommendation(topic["weak_proposal"], papers, mode=RunMode.SOTA)

    assert good.publication_status == "published"
    assert weak.publication_status == "needs_refinement"

    good_score = compute_verified_final_score(
        topic["good_proposal"]["scores"],
        sota_fit=0.8,
        novelty_verified=0.75,
        mode=RunMode.SOTA,
    )
    weak_score = compute_verified_final_score(
        topic["weak_proposal"]["scores"],
        sota_fit=0.2,
        novelty_verified=0.2,
        mode=RunMode.SOTA,
    )
    assert good_score > weak_score
