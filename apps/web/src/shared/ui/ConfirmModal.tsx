import type { ReactNode } from "react";
import { Button, Modal } from "react-bootstrap";
import { useTranslation } from "react-i18next";

interface ConfirmModalProps {
  show: boolean;
  onHide: () => void;
  title: string;
  children?: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  confirmVariant?: "primary" | "danger" | "secondary";
  loading?: boolean;
  size?: "sm" | "lg";
}

export function ConfirmModal({
  show,
  onHide,
  title,
  children,
  confirmLabel,
  cancelLabel,
  onConfirm,
  confirmVariant = "primary",
  loading = false,
  size,
}: ConfirmModalProps) {
  const { t } = useTranslation();

  return (
    <Modal show={show} onHide={onHide} centered size={size} className="app-modal app-modal--confirm">
      <Modal.Header closeButton>
        <Modal.Title>{title}</Modal.Title>
      </Modal.Header>
      {children ? <Modal.Body>{children}</Modal.Body> : null}
      <Modal.Footer>
        <Button variant="outline-secondary" onClick={onHide} disabled={loading}>
          {cancelLabel ?? t("common.cancel")}
        </Button>
        <Button variant={confirmVariant} onClick={onConfirm} disabled={loading}>
          {confirmLabel ?? t("common.confirm")}
        </Button>
      </Modal.Footer>
    </Modal>
  );
}

interface AlertModalProps {
  show: boolean;
  onHide: () => void;
  title: string;
  children?: ReactNode;
  okLabel?: string;
  variant?: "primary" | "danger";
}

/** Single-action modal (replaces `window.alert`). */
export function AlertModal({
  show,
  onHide,
  title,
  children,
  okLabel,
  variant = "primary",
}: AlertModalProps) {
  const { t } = useTranslation();

  return (
    <Modal show={show} onHide={onHide} centered className="app-modal app-modal--alert">
      <Modal.Header closeButton>
        <Modal.Title>{title}</Modal.Title>
      </Modal.Header>
      {children ? <Modal.Body>{children}</Modal.Body> : null}
      <Modal.Footer>
        <Button variant={variant} onClick={onHide}>
          {okLabel ?? t("common.ok")}
        </Button>
      </Modal.Footer>
    </Modal>
  );
}
