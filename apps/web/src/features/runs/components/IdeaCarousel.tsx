import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import type { Recommendation } from "@/shared/types/api";

interface IdeaCarouselProps {
  items: Recommendation[];
  activeIndex: number;
  ratedIds?: Set<string>;
  skippedIds?: Set<string>;
  onSelect: (index: number) => void;
}

export function IdeaCarousel({ items, activeIndex, ratedIds, skippedIds, onSelect }: IdeaCarouselProps) {
  const { t } = useTranslation();
  const trackRef = useRef<HTMLDivElement>(null);
  const slideRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const scrollingProgrammatically = useRef(false);
  const scrollEndTimer = useRef<number | null>(null);
  const [canPrev, setCanPrev] = useState(false);
  const [canNext, setCanNext] = useState(false);

  const updateEdgeHints = useCallback(() => {
    setCanPrev(activeIndex > 0);
    setCanNext(activeIndex < items.length - 1);
  }, [activeIndex, items.length]);

  const syncIndexFromScroll = useCallback(() => {
    const track = trackRef.current;
    if (!track || scrollingProgrammatically.current) {
      return;
    }

    const anchor = track.scrollLeft + 8;
    let closest = 0;
    let minDistance = Number.POSITIVE_INFINITY;

    slideRefs.current.forEach((slide, index) => {
      if (!slide) {
        return;
      }
      const slideStart = slide.offsetLeft;
      const distance = Math.abs(slideStart - anchor);
      if (distance < minDistance) {
        minDistance = distance;
        closest = index;
      }
    });

    if (closest !== activeIndex) {
      onSelect(closest);
    }
  }, [activeIndex, onSelect]);

  const handleScroll = useCallback(() => {
    if (scrollEndTimer.current) {
      window.clearTimeout(scrollEndTimer.current);
    }
    scrollEndTimer.current = window.setTimeout(syncIndexFromScroll, 80);
  }, [syncIndexFromScroll]);

  useEffect(() => {
    updateEdgeHints();
  }, [updateEdgeHints]);

  useEffect(() => {
    const slide = slideRefs.current[activeIndex];
    const track = trackRef.current;
    if (!slide || !track) {
      return;
    }

    scrollingProgrammatically.current = true;
    const target = slide.offsetLeft;

    track.scrollTo({ left: target, behavior: "smooth" });

    const timer = window.setTimeout(() => {
      scrollingProgrammatically.current = false;
    }, 350);

    return () => window.clearTimeout(timer);
  }, [activeIndex]);

  useEffect(() => {
    return () => {
      if (scrollEndTimer.current) {
        window.clearTimeout(scrollEndTimer.current);
      }
    };
  }, []);

  if (items.length === 0) {
    return null;
  }

  const showNav = items.length > 1;

  return (
    <div className="idea-carousel" aria-label={t("ideas.generatedIdeas")}>
      <div className="idea-carousel__header">
        <span className="idea-carousel__label">{t("ideas.generatedIdeas")}</span>
        <span className="idea-carousel__count">
          {t("ideas.countOfTotal", { current: activeIndex + 1, total: items.length })}
        </span>
      </div>

      <div className="idea-carousel__stage">
        {showNav ? (
          <button
            type="button"
            className="idea-carousel__nav idea-carousel__nav--prev"
            aria-label={t("ideas.previousIdea")}
            disabled={!canPrev}
            onClick={() => onSelect(activeIndex - 1)}
          >
            ‹
          </button>
        ) : null}
        <div
          ref={trackRef}
          className="idea-carousel__track"
          role="tablist"
          aria-label={t("ideas.swipeHint")}
          onScroll={handleScroll}
        >
          {items.map((item, index) => {
            const isActive = index === activeIndex;
            const isRated = ratedIds?.has(item.id) ?? false;
            const isSkipped = skippedIds?.has(item.id) ?? false;
            const score = item.final_score != null ? Math.round(item.final_score) : null;

            return (
              <button
                key={item.id}
                ref={(el) => {
                  slideRefs.current[index] = el;
                }}
                type="button"
                role="tab"
                aria-selected={isActive}
                aria-label={`${t("ideas.ideaNumber", { number: index + 1 })}: ${item.title}`}
                className={`idea-carousel__slide ${isActive ? "idea-carousel__slide--active" : ""} ${isRated ? "idea-carousel__slide--rated" : ""} ${isSkipped ? "idea-carousel__slide--skipped" : ""}`}
                onClick={() => onSelect(index)}
              >
                <span className="idea-carousel__slide-index">
                  {isRated ? <span className="idea-carousel__slide-check" aria-hidden>✓</span> : null}
                  {isSkipped ? <span className="idea-carousel__slide-skip" aria-hidden>–</span> : null}
                  {t("ideas.ideaNumber", { number: index + 1 })}
                </span>
                <span className="idea-carousel__slide-title">{item.title}</span>
                {item.technique_name ? (
                  <span className="idea-carousel__slide-meta">{item.technique_name}</span>
                ) : null}
                {score != null ? (
                  <span className="idea-carousel__slide-score">{t("ideas.score", { value: score })}</span>
                ) : null}
              </button>
            );
          })}
        </div>

        {showNav ? (
          <button
            type="button"
            className="idea-carousel__nav idea-carousel__nav--next"
            aria-label={t("ideas.nextIdea")}
            disabled={!canNext}
            onClick={() => onSelect(activeIndex + 1)}
          >
            ›
          </button>
        ) : null}
      </div>

    </div>
  );
}
