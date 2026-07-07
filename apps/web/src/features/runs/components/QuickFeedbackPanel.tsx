import { useMemo } from "react";
import { useTranslation } from "react-i18next";

import { InlineAlert } from "@/shared/ui/InlineAlert";

import { ChoiceChips } from "./feedback/ChoiceChips";
import { FeedbackField } from "./feedback/FeedbackField";
import { RatingStars } from "./feedback/RatingStars";

export type WouldUse = "yes" | "maybe" | "no";

interface QuickFeedbackPanelProps {
  rating: number | null;
  wouldUse: WouldUse;
  submitting: boolean;
  message: string | null;
  error: string | null;
  onStarClick: (value: number) => void;
  onWouldUseChange: (value: WouldUse) => void;
}

export function QuickFeedbackPanel({
  rating,
  wouldUse,
  submitting,
  message,
  error,
  onStarClick,
  onWouldUseChange,
}: QuickFeedbackPanelProps) {
  const { t } = useTranslation();

  const paperOptions = useMemo(
    () =>
      (["yes", "maybe", "no"] as const).map((value) => ({
        value,
        label: t(`common.${value}`),
      })),
    [t],
  );

  return (
    <section className="idea-feedback" aria-label={t("ideas.rateIdea")}>
      <FeedbackField label={t("ideas.quickRatingLabel")}>
        <RatingStars
          value={rating}
          disabled={submitting}
          ariaLabel={t("ideas.quickRatingLabel")}
          getStarLabel={(star) => t("ideas.rateValue", { value: star })}
          onChange={onStarClick}
        />
      </FeedbackField>

      <FeedbackField label={t("ideas.useInPaper")}>
        <ChoiceChips
          options={paperOptions}
          value={wouldUse}
          disabled={submitting}
          ariaLabel={t("ideas.useInPaper")}
          onChange={onWouldUseChange}
        />
      </FeedbackField>

      {message ? (
        <p className="idea-feedback__status" aria-live="polite">
          {message}
        </p>
      ) : null}
      {error ? <InlineAlert variant="danger">{error}</InlineAlert> : null}
    </section>
  );
}
