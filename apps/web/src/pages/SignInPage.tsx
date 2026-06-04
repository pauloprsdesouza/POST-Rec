import type { FormEvent } from "react";
import { useState } from "react";
import { Alert, Button, Form, Nav } from "react-bootstrap";
import { Trans, useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { AuthShell } from "../components/layout/AuthShell";
import { useAuth } from "../contexts/AuthContext";
import { useApiHealth } from "../hooks/useApiHealth";
import { authService } from "../services";
import { HttpError } from "../services/http/HttpClient";

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
  const [whatsappOptIn, setWhatsappOptIn] = useState(true);
  const [code, setCode] = useState("");

  const [phoneHint, setPhoneHint] = useState<string | null>(null);
  const [devCode, setDevCode] = useState<string | null>(null);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const resetOtpStep = () => {
    setStep("credentials");
    setCode("");
    setDevCode(null);
    setPhoneHint(null);
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
          ? await authService.register(fullName.trim(), email.trim(), phone.trim(), whatsappOptIn)
          : await authService.requestLoginOtp(email.trim());

      setDevCode(response.dev_code ?? null);
      setPhoneHint(response.phone_hint ?? null);
      setInfoMessage(response.message);
      setStep("otp");
    } catch (err) {
      setError(err instanceof HttpError ? err.message : t("auth.errorSendCode"));
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const response = await authService.verifyOtp(email.trim(), code.trim());
      await signIn(response);
      navigate("/");
    } catch (err) {
      setError(err instanceof HttpError ? err.message : t("auth.errorVerify"));
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setError(null);
    setLoading(true);
    try {
      const response =
        mode === "register"
          ? await authService.register(fullName.trim(), email.trim(), phone.trim(), whatsappOptIn)
          : await authService.requestLoginOtp(email.trim());
      setDevCode(response.dev_code ?? null);
      setPhoneHint(response.phone_hint ?? null);
      setInfoMessage(response.message);
    } catch (err) {
      setError(err instanceof HttpError ? err.message : t("auth.errorResend"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell online={online}>
      {step === "credentials" ? (
        <>
          <Nav variant="pills" className="auth-tabs mb-4">
            <Nav.Item>
              <Nav.Link active={mode === "signin"} onClick={() => switchMode("signin")}>
                {t("auth.signIn")}
              </Nav.Link>
            </Nav.Item>
            <Nav.Item>
              <Nav.Link active={mode === "register"} onClick={() => switchMode("register")}>
                {t("auth.createAccount")}
              </Nav.Link>
            </Nav.Item>
          </Nav>

          {error ? <Alert variant="danger">{error}</Alert> : null}

          <Form onSubmit={handleRequestOtp}>
            {mode === "register" ? (
              <>
                <Form.Group className="mb-3">
                  <Form.Label>{t("auth.fullName")}</Form.Label>
                  <Form.Control
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder={t("auth.fullNamePlaceholder")}
                    required
                    autoComplete="name"
                  />
                </Form.Group>
                <Form.Group className="mb-3">
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
                <Form.Group className="mb-3">
                  <Form.Label>{t("auth.whatsappNumber")}</Form.Label>
                  <Form.Control
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder={t("auth.whatsappPlaceholder")}
                    required
                    autoComplete="tel"
                  />
                  <Form.Text>{t("auth.whatsappHint")}</Form.Text>
                </Form.Group>
                <Form.Check
                  type="switch"
                  id="whatsapp-opt-in"
                  className="mb-4"
                  label={t("auth.whatsappOptIn")}
                  checked={whatsappOptIn}
                  onChange={(e) => setWhatsappOptIn(e.target.checked)}
                />
              </>
            ) : (
              <>
                <p className="text-secondary small mb-3">{t("auth.signInHint")}</p>
                <Form.Group className="mb-4">
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
              </>
            )}

            <Button type="submit" variant="primary" className="w-100" disabled={loading || !online}>
              {loading
                ? t("auth.sending")
                : mode === "register"
                  ? t("auth.createAccountAndSend")
                  : t("auth.sendSignInCode")}
            </Button>

            {mode === "signin" ? (
              <p className="text-secondary small mt-3 mb-0">
                {t("auth.newHere")}{" "}
                <button type="button" className="btn btn-link p-0 align-baseline" onClick={() => switchMode("register")}>
                  {t("auth.createAnAccount")}
                </button>{" "}
                {t("auth.withContactDetails")}
              </p>
            ) : (
              <p className="text-secondary small mt-3 mb-0">
                {t("auth.alreadyRegistered")}{" "}
                <button type="button" className="btn btn-link p-0 align-baseline" onClick={() => switchMode("signin")}>
                  {t("auth.signInWithEmail")}
                </button>
                .
              </p>
            )}
          </Form>
        </>
      ) : (
        <>
          {error ? <Alert variant="danger">{error}</Alert> : null}
          {infoMessage ? <Alert variant="success">{infoMessage}</Alert> : null}
          {devCode ? (
            <Alert variant="info">
              <Trans i18nKey="auth.devModeCode" values={{ code: devCode }} components={{ strong: <strong /> }} />
            </Alert>
          ) : null}

          <Form onSubmit={handleVerifyOtp}>
            <p className="text-secondary small mb-1">
              <Trans i18nKey="auth.codeSentFor" values={{ email }} components={{ strong: <strong /> }} />
              {phoneHint ? (
                <>
                  {" "}
                  <Trans i18nKey="auth.codeSentToWhatsapp" values={{ phone: phoneHint }} components={{ strong: <strong /> }} />
                </>
              ) : null}
              .
            </p>
            <p className="text-secondary small mb-3">{t("auth.changePhoneLater")}</p>

            <Form.Group className="mb-4">
              <Form.Label>{t("auth.verificationCode")}</Form.Label>
              <Form.Control
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder={t("auth.codePlaceholder")}
                required
                autoFocus
                inputMode="numeric"
                autoComplete="one-time-code"
              />
            </Form.Group>

            <Button type="submit" variant="primary" className="w-100 mb-2" disabled={loading}>
              {loading ? t("auth.verifying") : t("auth.verifyAndContinue")}
            </Button>
            <div className="d-flex gap-2">
              <Button
                type="button"
                variant="outline-secondary"
                className="flex-grow-1"
                onClick={resetOtpStep}
                disabled={loading}
              >
                {t("common.back")}
              </Button>
              <Button type="button" variant="outline-primary" className="flex-grow-1" onClick={handleResend} disabled={loading}>
                {t("auth.resendCode")}
              </Button>
            </div>
          </Form>
        </>
      )}
    </AuthShell>
  );
}
