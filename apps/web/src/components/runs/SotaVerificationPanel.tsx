import { Badge } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import type { Recommendation, SotaAnchor } from "../../types/api";
import type { SourceDocument } from "../../types/api";

interface SotaVerificationPanelProps {
  recommendation: Recommendation;
  sources?: SourceDocument[];
}

export function SotaVerificationPanel({ recommendation, sources = [] }: SotaVerificationPanelProps) {
  const { t } = useTranslation();

  const hasSotaContent =
    recommendation.sota_summary ||
    recommendation.novelty_delta ||
    recommendation.closest_prior_work ||
    recommendation.differentiation_score_rationale ||
    recommendation.facet_deltas ||
    recommendation.sota_fit != null ||
    recommendation.novelty_verified != null ||
    recommendation.facet_novelty_index != null ||
    recommendation.gap_alignment_score != null ||
    recommendation.embedding_distance != null;

  if (!hasSotaContent) {
    return null;
  }

  const sourceByTitle = new Map(
    sources.filter((s) => s.title).map((s) => [s.title!.toLowerCase(), s]),
  );

  return (
    <div className="sota-panel">
      <div className="sota-panel__header">
        <h3 className="h6 mb-0">{t("ideas.sotaVerification.title")}</h3>
        <div className="sota-panel__badges">
          {recommendation.critic_accepted != null ? (
            <Badge bg={recommendation.critic_accepted ? "success" : "warning"}>
              {recommendation.critic_accepted
                ? t("ideas.sotaVerification.criticPassed")
                : t("ideas.sotaVerification.criticReview")}
            </Badge>
          ) : null}
          {recommendation.status === "needs_refinement" ? (
            <Badge bg="warning">{t("ideas.refinement.badge")}</Badge>
          ) : null}
        </div>
      </div>

      {recommendation.sota_summary ? (
        <SotaBlock label={t("ideas.sotaVerification.sotaSummary")} value={recommendation.sota_summary} />
      ) : null}

      {recommendation.novelty_delta ? (
        <SotaBlock label={t("ideas.sotaVerification.noveltyDelta")} value={recommendation.novelty_delta} />
      ) : null}

      {recommendation.closest_prior_work ? (
        <SotaBlock
          label={t("ideas.sotaVerification.closestPriorWork")}
          value={recommendation.closest_prior_work}
        />
      ) : null}

      {recommendation.differentiation_score_rationale ? (
        <SotaBlock
          label={t("ideas.sotaVerification.differentiationRationale")}
          value={recommendation.differentiation_score_rationale}
        />
      ) : null}

      {(recommendation.sota_fit != null ||
        recommendation.novelty_verified != null ||
        recommendation.facet_novelty_index != null ||
        recommendation.gap_alignment_score != null ||
        recommendation.fggv_score != null ||
        recommendation.embedding_distance != null ||
        recommendation.recency_gap != null) && (
        <div className="sota-panel__metrics">
          {recommendation.fggv_score != null ? (
            <MetricBar label={t("ideas.sotaVerification.fggvScore")} value={recommendation.fggv_score} />
          ) : null}
          {recommendation.facet_novelty_index != null ? (
            <MetricBar
              label={t("ideas.sotaVerification.facetNoveltyIndex")}
              value={recommendation.facet_novelty_index}
            />
          ) : null}
          {recommendation.scores?.false_novel_facet_count != null ? (
            <div className="sota-panel__metric-note text-secondary small">
              {t("ideas.sotaVerification.falseNovelFacets", {
                count: recommendation.scores.false_novel_facet_count,
              })}
            </div>
          ) : null}
          {recommendation.gap_alignment_score != null ? (
            <MetricBar
              label={t("ideas.sotaVerification.gapAlignmentScore")}
              value={recommendation.gap_alignment_score}
            />
          ) : null}
          {recommendation.sota_fit != null ? (
            <MetricBar label={t("ideas.sotaVerification.sotaFit")} value={recommendation.sota_fit} />
          ) : null}
          {recommendation.novelty_verified != null ? (
            <MetricBar
              label={t("ideas.sotaVerification.noveltyVerified")}
              value={recommendation.novelty_verified}
            />
          ) : null}
          {recommendation.embedding_distance != null ? (
            <MetricBar
              label={t("ideas.sotaVerification.embeddingDistance")}
              value={recommendation.embedding_distance}
              invert
            />
          ) : null}
          {recommendation.recency_gap != null ? (
            <MetricBar label={t("ideas.sotaVerification.recencyGap")} value={recommendation.recency_gap} />
          ) : null}
        </div>
      )}

      {recommendation.validation_issues?.length ? (
        <div className="sota-panel__issues">
          <div className="idea-block__label">{t("ideas.sotaVerification.validationIssues")}</div>
          <ul className="idea-block__list">
            {recommendation.validation_issues.map((issue) => (
              <li key={issue}>{issue}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {recommendation.facet_deltas ? (
        <div className="sota-panel__facets">
          <div className="idea-block__label">{t("ideas.sotaVerification.facetDeltas")}</div>
          <ul className="idea-block__list">
            {Object.entries(recommendation.facet_deltas).map(([key, value]) =>
              value ? (
                <li key={key}>
                  <strong>{key}:</strong> {value}
                </li>
              ) : null,
            )}
          </ul>
        </div>
      ) : null}

      {recommendation.aligned_gaps?.length ? (
        <div className="sota-panel__gaps">
          <div className="idea-block__label">{t("ideas.sotaVerification.alignedGaps")}</div>
          <ul className="idea-block__list">
            {recommendation.aligned_gaps.map((gap) => (
              <li key={gap}>{gap}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {recommendation.sota_anchors?.length ? (
        <div className="sota-panel__anchors">
          <div className="idea-block__label">{t("ideas.sotaVerification.sotaAnchors")}</div>
          <ul className="idea-block__list">
            {recommendation.sota_anchors.map((anchor) => (
              <li key={`${anchor.title}-${anchor.year ?? "na"}`}>
                <AnchorItem anchor={anchor} source={sourceByTitle.get((anchor.title ?? "").toLowerCase())} />
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

function SotaBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="idea-block">
      <div className="idea-block__label">{label}</div>
      <p className="idea-block__text">{value}</p>
    </div>
  );
}

function MetricBar({
  label,
  value,
  invert = false,
}: {
  label: string;
  value: number;
  invert?: boolean;
}) {
  const display = invert ? Math.max(0, 100 - value) : value;
  return (
    <div className="idea-scores__item">
      <div className="idea-scores__label">
        {label} <strong>{Math.round(display)}</strong>
      </div>
      <div className="progress idea-scores__bar">
        <div className="progress-bar" style={{ width: `${Math.min(display, 100)}%` }} />
      </div>
    </div>
  );
}

function AnchorItem({
  anchor,
  source,
}: {
  anchor: SotaAnchor;
  source?: SourceDocument;
}) {
  const role = anchor.role?.replace(/_/g, " ");
  const content = (
    <>
      {anchor.title}
      {anchor.year ? ` (${anchor.year})` : ""}
      {role ? ` — ${role}` : ""}
    </>
  );

  if (source?.url || anchor.url) {
    return (
      <a href={source?.url ?? anchor.url ?? "#"} target="_blank" rel="noreferrer">
        {content}
      </a>
    );
  }

  return <span>{content}</span>;
}
