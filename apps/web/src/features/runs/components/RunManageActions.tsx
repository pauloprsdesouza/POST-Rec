import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { runService } from "@/shared/api";
import type { RecommendationRun } from "@/shared/types/api";
import { ConfirmModal } from "@/shared/ui/ConfirmModal";
import { InlineAlert } from "@/shared/ui/InlineAlert";
import { Panel } from "@/shared/ui/Panel";
import { canCancelRun, canDismissRun, canRetryRun } from "@/features/runs/utils/runs";

type PendingAction = "archive" | "remove" | null;

interface RunManageActionsProps {
  token: string;
  run: RecommendationRun;
  onRunUpdated?: (run: RecommendationRun) => void;
  onRunsChanged?: () => void;
}

export function RunManageActions({ token, run, onRunUpdated, onRunsChanged }: RunManageActionsProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const runId = String(run.id);

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cancelConfirmOpen, setCancelConfirmOpen] = useState(false);
  const [pendingAction, setPendingAction] = useState<PendingAction>(null);
  const [learnedTopics, setLearnedTopics] = useState<string[]>([]);
  const [selectedTopics, setSelectedTopics] = useState<Set<string>>(new Set());
  const [loadingPreview, setLoadingPreview] = useState(false);

  const showRetry = canRetryRun(run);
  const showCancel = canCancelRun(run.status);
  const showDismiss = canDismissRun(run.status);

  const resetPending = useCallback(() => {
    setPendingAction(null);
    setLearnedTopics([]);
    setSelectedTopics(new Set());
    setError(null);
  }, []);

  const openDismissFlow = useCallback(
    async (action: PendingAction) => {
      setError(null);
      setPendingAction(action);
      setLoadingPreview(true);
      try {
        const preview = await runService.getRunCleanupPreview(token, runId);
        setLearnedTopics(preview.learned_topics);
        setSelectedTopics(new Set());
      } catch (err) {
        setError(err instanceof Error ? err.message : t("runs.actions.error"));
        setPendingAction(null);
      } finally {
        setLoadingPreview(false);
      }
    },
    [runId, t, token],
  );

  const toggleTopic = useCallback((topic: string) => {
    setSelectedTopics((current) => {
      const next = new Set(current);
      if (next.has(topic)) {
        next.delete(topic);
      } else {
        next.add(topic);
      }
      return next;
    });
  }, []);

  const confirmCancel = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      await runService.cancelRun(token, runId);
      const updated = await runService.getRun(token, runId);
      onRunUpdated?.(updated);
      onRunsChanged?.();
      setCancelConfirmOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("runs.actions.error"));
    } finally {
      setBusy(false);
    }
  }, [onRunUpdated, onRunsChanged, runId, t, token]);

  const handleRetry = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      await runService.retryRun(token, runId);
      const updated = await runService.getRun(token, runId);
      onRunUpdated?.(updated);
      onRunsChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("runs.actions.error"));
    } finally {
      setBusy(false);
    }
  }, [onRunUpdated, onRunsChanged, runId, t, token]);

  const confirmDismiss = useCallback(async () => {
    if (!pendingAction) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const payload = { remove_learned_topics: Array.from(selectedTopics) };
      if (pendingAction === "archive") {
        await runService.archiveRun(token, runId, payload);
      } else {
        await runService.removeRun(token, runId, payload);
      }
      onRunsChanged?.();
      navigate("/runs");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("runs.actions.error"));
    } finally {
      setBusy(false);
    }
  }, [navigate, onRunsChanged, pendingAction, runId, selectedTopics, t, token]);

  if (!showRetry && !showCancel && !showDismiss) {
    return null;
  }

  const dismissTitle =
    pendingAction === "archive" ? t("runs.actions.archive") : t("runs.actions.remove");
  const dismissConfirmLabel =
    pendingAction === "archive" ? t("runs.actions.archive") : t("runs.actions.remove");

  return (
    <Panel as="section" className="run-manage" aria-label={t("runs.actions.title")}>
      <h2 className="run-manage__title">{t("runs.actions.title")}</h2>

      {error ? <InlineAlert variant="danger">{error}</InlineAlert> : null}

      <div className="run-manage__actions">
        {showRetry ? (
          <button type="button" className="btn btn-primary" onClick={() => void handleRetry()} disabled={busy}>
            {t("runs.actions.retry")}
          </button>
        ) : null}
        {showCancel ? (
          <button
            type="button"
            className="btn btn-outline-secondary"
            onClick={() => setCancelConfirmOpen(true)}
            disabled={busy}
          >
            {t("runs.actions.cancel")}
          </button>
        ) : null}
        {showDismiss ? (
          <>
            <button
              type="button"
              className="btn btn-outline-secondary"
              onClick={() => void openDismissFlow("archive")}
              disabled={busy}
            >
              {t("runs.actions.archive")}
            </button>
            <button
              type="button"
              className="btn btn-outline-danger"
              onClick={() => void openDismissFlow("remove")}
              disabled={busy}
            >
              {t("runs.actions.remove")}
            </button>
          </>
        ) : null}
      </div>

      <ConfirmModal
        show={cancelConfirmOpen}
        onHide={() => setCancelConfirmOpen(false)}
        title={t("runs.actions.cancel")}
        confirmLabel={t("runs.actions.cancel")}
        confirmVariant="danger"
        loading={busy}
        onConfirm={() => void confirmCancel()}
      >
        <p className="mb-0">{t("runs.actions.cancelConfirm")}</p>
      </ConfirmModal>

      <ConfirmModal
        show={pendingAction !== null}
        onHide={resetPending}
        title={dismissTitle}
        confirmLabel={dismissConfirmLabel}
        confirmVariant={pendingAction === "remove" ? "danger" : "primary"}
        loading={busy || loadingPreview}
        onConfirm={() => void confirmDismiss()}
      >
        <div className="run-manage__confirm">
          <p className="run-manage__confirm-text">
            {pendingAction === "archive"
              ? t("runs.actions.archiveConfirm")
              : t("runs.actions.removeConfirm")}
          </p>

          {loadingPreview ? (
            <p className="run-manage__hint">{t("runs.actions.loadingLearnedTopics")}</p>
          ) : learnedTopics.length > 0 ? (
            <fieldset className="run-manage__topics">
              <legend>{t("runs.actions.learnedTopicsLegend")}</legend>
              <p className="run-manage__hint">{t("runs.actions.learnedTopicsHint")}</p>
              <ul className="run-manage__topic-list">
                {learnedTopics.map((topic) => (
                  <li key={topic}>
                    <label className="run-manage__topic-label">
                      <input
                        type="checkbox"
                        checked={selectedTopics.has(topic)}
                        onChange={() => toggleTopic(topic)}
                        disabled={busy}
                      />
                      <span>{topic}</span>
                    </label>
                  </li>
                ))}
              </ul>
            </fieldset>
          ) : null}
        </div>
      </ConfirmModal>
    </Panel>
  );
}
