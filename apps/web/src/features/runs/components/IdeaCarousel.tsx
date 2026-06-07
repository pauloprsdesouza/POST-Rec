import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import type { Recommendation } from "@/shared/types/api";

interface IdeaCarouselProps {
  items: Recommendation[];
  activeIndex: number;
  onSelect: (index: number) => void;
}

export function IdeaCarousel({ items, activeIndex, onSelect }: IdeaCarouselProps) {
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

  return (
    <div className="idea-carousel" aria-label={t("ideas.generatedIdeas")}>
      <div className="idea-carousel__header">
        <span className="idea-carousel__label">{t("ideas.generatedIdeas")}</span>
        <span className="idea-carousel__count">
          {t("ideas.countOfTotal", { current: activeIndex + 1, total: items.length })}
        </span>
      </div>

      <div className="idea-carousel__stage">
        <div
          className={`idea-carousel__fade idea-carousel__fade--left ${canPrev ? "idea-carousel__fade--visible" : ""}`}
          aria-hidden
        />
        <div
          className={`idea-carousel__fade idea-carousel__fade--right ${canNext ? "idea-carousel__fade--visible" : ""}`}
          aria-hidden
        />

        <div
          ref={trackRef}
          className="idea-carousel__track"
          role="tablist"
          aria-label={t("ideas.swipeHint")}
          onScroll={handleScroll}
        >
          {items.map((item, index) => {
            const isActive = index === activeIndex;
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
                className={`idea-carousel__slide ${isActive ? "idea-carousel__slide--active" : ""}`}
                onClick={() => onSelect(index)}
              >
                <span className="idea-carousel__slide-index">{t("ideas.ideaNumber", { number: index + 1 })}</span>
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
      </div>

      <div className="idea-carousel__dots" role="tablist" aria-label={t("ideas.swipeHint")}>
        {items.map((item, index) => (
          <button
            key={item.id}
            type="button"
            role="tab"
            aria-selected={index === activeIndex}
            aria-label={t("ideas.goToIdea", { number: index + 1 })}
            className={`idea-carousel__dot ${index === activeIndex ? "idea-carousel__dot--active" : ""}`}
            onClick={() => onSelect(index)}
          />
        ))}
      </div>
    </div>
  );
}
