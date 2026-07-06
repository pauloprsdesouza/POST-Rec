import type { FormEvent } from "react";
import { useCallback, useRef, useState } from "react";
import { Button, Form } from "react-bootstrap";
import { Trans, useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { AuthShell } from "@/shared/layout/AuthShell";
import { InlineAlert } from "@/shared/ui/InlineAlert";
import { OtpInput } from "@/shared/ui/OtpInput";
import { PhoneInput } from "@/shared/ui/PhoneInput";
import { useAuth } from "@/features/auth/context/AuthContext";
import { useApiHealth } from "@/shared/hooks/useApiHealth";
import { authService } from "@/features/auth/api/authService";
import { getErrorMessage } from "@/shared/api/errors";

type AuthMode = "signin" | "register";
type Step = "credentials" | "otp";

export function SignInPage() {
  const { t } = useTranslation();
  const { signIn } = useAuth();
  const online = useApiHealth();
  const navigate = useNavigate();

  const [mode, setMode] = useState<AuthMode>("signin");
  const [step, setStep] = useState<Step>("credentials");

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [whatsappOptIn, setWhatsappOptIn] = useState(false);
  const [code, setCode] = useState("");

  const [devCode, setDevCode] = useState<string | null>(null);
  const [deliveryHint, setDeliveryHint] = useState<string | null>(null);
  const [deliveryChannel, setDeliveryChannel] = useState<"email" | "whatsapp">("email");
  const [infoMessage, setInfoMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const verifyingRef = useRef(false);

  const resetOtpStep = () => {
    setStep("credentials");
    setCode("");
    setDevCode(null);
    setDeliveryHint(null);
    setDeliveryChannel("email");
    setInfoMessage(null);
    setError(null);
  };

  const switchMode = (next: AuthMode) => {
    setMode(next);
    resetOtpStep();
  };

  const handleRequestOtp = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setInfoMessage(null);
    setLoading(true);

    try {
      const response =
        mode === "register"
          ? await authService.register(
              fullName.trim(),
              email.trim(),
              phone.trim() || null,
              whatsappOptIn,
            )
          : await authService.requestLoginOtp(email.trim());

      setDevCode(response.dev_code ?? null);
      setDeliveryHint(response.phone_hint ?? response.email_hint ?? null);
      setDeliveryChannel(response.phone_hint ? "whatsapp" : "email");
      setInfoMessage(response.message);
      setStep("otp");
    } catch (err) {
      setError(getErrorMessage(err, t("auth.errorSendCode")));
    } finally {
      setLoading(false);
    }
  };

  const verifyOtpCode = useCallback(
    async (otpCode: string) => {
      const trimmed = otpCode.trim();
      if (trimmed.length < 6 || verifyingRef.current || loading) {
        return;
      }

      verifyingRef.current = true;
      setError(null);
      setLoading(true);

      try {
        const response = await authService.verifyOtp(email.trim(), trimmed);
        await signIn(response);
        navigate("/");
      } catch (err) {
        setError(getErrorMessage(err, t("auth.errorVerify")));
        setCode("");
      } finally {
        verifyingRef.current = false;
        setLoading(false);
      }
    },
    [email, loading, navigate, signIn, t],
  );

  const handleResend = async () => {
    setError(null);
    setLoading(true);
    try {
      const response = await authService.requestLoginOtp(email.trim());
      setDevCode(response.dev_code ?? null);
      setDeliveryHint(response.phone_hint ?? response.email_hint ?? null);
      setDeliveryChannel(response.phone_hint ? "whatsapp" : "email");
      setInfoMessage(response.message);
    } catch (err) {
      setError(getErrorMessage(err, t("auth.errorResend")));
    } finally {
      setLoading(false);
    }
  };

  const credentialsTitle = mode === "register" ? t("auth.registerTitle") : t("auth.signInTitle");
  const credentialsSubtitle = mode === "register" ? t("auth.registerSubtitle") : t("auth.signInSubtitle");

  return (
    <AuthShell online={online}>
      {step === "credentials" ? (
        <>
          <header className="auth-form__header">
            <h1 className="auth-form__title">{credentialsTitle}</h1>
            <p className="auth-form__subtitle">{credentialsSubtitle}</p>
          </header>

          <div className="auth-mode-switch">
            <div className="segmented-control" role="tablist" aria-label={t("auth.signIn")}>
              <button
                type="button"
                role="tab"
                aria-selected={mode === "signin"}
                className={`segmented-control__item ${mode === "signin" ? "segmented-control__item--selected" : ""}`}
                onClick={() => switchMode("signin")}
              >
                {t("auth.signIn")}
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={mode === "register"}
                className={`segmented-control__item ${mode === "register" ? "segmented-control__item--selected" : ""}`}
                onClick={() => switchMode("register")}
              >
                {t("auth.createAccount")}
              </button>
            </div>
          </div>

          {error ? <InlineAlert variant="danger">{error}</InlineAlert> : null}

          <Form onSubmit={handleRequestOtp} className="form-stack">
            {mode === "register" ? (
              <>
                <Form.Group className="field-group">
                  <Form.Label>{t("auth.fullName")}</Form.Label>
                  <Form.Control
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder={t("auth.fullNamePlaceholder")}
                    required
                    autoComplete="name"
                  />
                </Form.Group>
                <Form.Group className="field-group">
                  <Form.Label>{t("auth.email")}</Form.Label>
                  <Form.Control
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder={t("auth.emailPlaceholder")}
                    required
                    autoComplete="email"
                  />
                </Form.Group>
                <Form.Group className="field-group">
                  <Form.Label>{t("auth.whatsappNumber")}</Form.Label>
                  <PhoneInput
                    value={phone}
                    onChange={(nextPhone) => {
                      setPhone(nextPhone);
                      if (!nextPhone.trim()) {
                        setWhatsappOptIn(false);
                      }
                    }}
                    placeholder={t("auth.whatsappPlaceholder")}
                    required={whatsappOptIn}
                    autoComplete="tel"
                  />
                  <Form.Text>{t("auth.whatsappHintOptional")}</Form.Text>
                </Form.Group>
                <Form.Check
                  type="switch"
                  id="whatsapp-opt-in"
                  label={t("auth.whatsappOptInShort")}
                  checked={whatsappOptIn}
                  onChange={(e) => setWhatsappOptIn(e.target.checked)}
                  disabled={!phone.trim()}
                />
                <Form.Text className="d-block">
                  {phone.trim()
                    ? whatsappOptIn
                      ? t("auth.whatsappOptInEnabledHint")
                      : t("auth.whatsappOptInDisabledHint")
                    : t("auth.whatsappOptInRequiresPhone")}
                </Form.Text>
              </>
            ) : (
              <Form.Group className="field-group">
                <Form.Label>{t("auth.email")}</Form.Label>
                <Form.Control
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={t("auth.emailPlaceholder")}
                  required
                  autoComplete="email"
                  autoFocus
                />
              </Form.Group>
            )}

            <div className="auth-form__cta">
              <Button type="submit" variant="primary" className="w-100" disabled={loading || online === false}>
                {loading
                  ? t("auth.sending")
                  : mode === "register"
                    ? t("auth.createAccountAndSend")
                    : t("auth.sendSignInCode")}
              </Button>
              <p className="auth-trust-line">{t("auth.trustLine")}</p>
            </div>
          </Form>
        </>
      ) : (
        <div className="auth-otp-step">
          <button type="button" className="auth-otp-step__back" onClick={resetOtpStep} disabled={loading}>
            ← {t("common.back")}
          </button>

          <header className="auth-form__header">
            <h1 className="auth-form__title">{t("auth.otpTitle")}</h1>
            <p className="auth-form__subtitle">{t("auth.otpSubtitle")}</p>
          </header>

          <div className="auth-otp-step__destination">
            <span className="auth-otp-step__destination-label">{t("auth.otpSentTo")}</span>
            <span className="auth-otp-step__destination-value">{deliveryHint ?? email}</span>
            {deliveryChannel === "whatsapp" ? (
              <span className="auth-otp-step__destination-meta">{t("auth.otpWhatsappChannel")}</span>
            ) : (
              <span className="auth-otp-step__destination-meta">{t("auth.otpEmailChannel")}</span>
            )}
          </div>

          {(error || infoMessage || devCode) && (
            <div className="auth-otp-step__alerts">
              {error ? <InlineAlert variant="danger">{error}</InlineAlert> : null}
              {infoMessage ? <InlineAlert variant="success">{infoMessage}</InlineAlert> : null}
              {devCode ? (
                <InlineAlert variant="info">
                  <Trans i18nKey="auth.devModeCode" values={{ code: devCode }} components={{ strong: <strong /> }} />
                </InlineAlert>
              ) : null}
            </div>
          )}

          <div className="form-stack auth-otp-step__form">
            <Form.Group className="field-group auth-otp-step__field">
              <Form.Label className="visually-hidden">{t("auth.verificationCode")}</Form.Label>
              <OtpInput
                id="auth-otp"
                value={code}
                onChange={setCode}
                onComplete={verifyOtpCode}
                autoFocus
                disabled={loading}
                aria-label={t("auth.verificationCode")}
              />
              {loading ? (
                <p className="auth-otp-step__status" role="status" aria-live="polite">
                  {t("auth.verifying")}
                </p>
              ) : null}
            </Form.Group>

            <p className="auth-otp-step__help">
              {t("auth.otpNoCode")}{" "}
              <button type="button" className="auth-form__text-link" onClick={handleResend} disabled={loading}>
                {t("auth.resendCode")}
              </button>
            </p>
          </div>
        </div>
      )}
    </AuthShell>
  );
}
