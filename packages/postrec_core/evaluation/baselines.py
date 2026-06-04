"""Baseline method identifiers for empirical comparison."""

from enum import StrEnum


class BaselineMethod(StrEnum):
    """Methods comparable in offline / human evaluation studies."""

    B1_QUICK = "b1_quick"
    B2_SOTA_PIPELINE = "b2_sota_pipeline"
    B3_RAG_NO_VERIFY = "b3_rag_no_verify"
    M_FGGV = "m_fggv"
    M_FGGV_NO_GFA = "m_fggv_no_gfa"
    M_FGGV_NO_CFN = "m_fggv_no_cfn"
    M_FGGV_NO_SATURATION = "m_fggv_no_saturation"


BASELINE_DESCRIPTIONS: dict[BaselineMethod, str] = {
    BaselineMethod.B1_QUICK: "Single-pass RAG with post-hoc document novelty.",
    BaselineMethod.B2_SOTA_PIPELINE: "Landscape → gap matrix → proposals with document-level novelty.",
    BaselineMethod.B3_RAG_NO_VERIFY: "Single-pass RAG without verification (lower bound).",
    BaselineMethod.M_FGGV: "FGGV v2: SA-FNI + GFA + facet critic + FDS.",
    BaselineMethod.M_FGGV_NO_GFA: "Ablation: FGGV without gap-facet alignment term.",
    BaselineMethod.M_FGGV_NO_CFN: "Ablation: FGGV using document novelty instead of facet CFN.",
    BaselineMethod.M_FGGV_NO_SATURATION: "Ablation: FGGV without saturation-aware facet weighting.",
}

CORE_METHODS = (
    BaselineMethod.B1_QUICK,
    BaselineMethod.B2_SOTA_PIPELINE,
    BaselineMethod.B3_RAG_NO_VERIFY,
    BaselineMethod.M_FGGV,
)

ABLATION_METHODS = (
    BaselineMethod.M_FGGV_NO_GFA,
    BaselineMethod.M_FGGV_NO_CFN,
    BaselineMethod.M_FGGV_NO_SATURATION,
)
