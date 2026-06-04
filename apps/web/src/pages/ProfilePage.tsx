import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { Alert, Button, Card, Col, Form, Nav, Row, Tab } from "react-bootstrap";
import { useTranslation } from "react-i18next";
import { useNavigate, useSearchParams } from "react-router-dom";

import { ConsentPanel } from "../components/profile/ConsentPanel";
import {
  emptyRecommendationDefaults,
  RecommendationPreferencesForm,
} from "../components/profile/RecommendationPreferencesForm";
import { PageHeader } from "../components/ui/PageHeader";
import { LanguageSwitcher } from "../components/ui/LanguageSwitcher";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ACADEMIC_LEVELS, DEFAULT_SEED_TOPICS, EXPERIENCE_LEVELS } from "../constants";
import { useEnumLabel } from "../i18n/useEnumLabel";
import i18n from "../i18n";
import { useAuth } from "../contexts/AuthContext";
import { accountService, profileService, sessionService } from "../services";
import { HttpError } from "../services/http/HttpClient";
import type { RecommendationDefaults, UserAccount, UserConsentStatus, UserProfile } from "../types/api";

const TABS = ["account", "research", "preferences", "consent"] as const;
type ProfileTab = (typeof TABS)[number];

function isValidTab(value: string | null): value is ProfileTab {
  return TABS.includes(value as ProfileTab);
}

export function ProfilePage() {
  const { t } = useTranslation();
  const academicLabel = useEnumLabel("enums.academicLevel");
  const experienceLabel = useEnumLabel("enums.experience");
  const { accessToken, user, sessionId, setSessionId, completeProfile, updateUser } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const tabParam = searchParams.get("tab");
  const activeTab: ProfileTab = isValidTab(tabParam) ? tabParam : "account";

  const [account, setAccount] = useState<UserAccount>({});
  const [profile, setProfile] = useState<UserProfile>({});
  const [consentStatus, setConsentStatus] = useState<UserConsentStatus | null>(null);
  const [preferences, setPreferences] = useState<RecommendationDefaults>(emptyRecommendationDefaults());

  const [loading, setLoading] = useState(true);
  const [savingAccount, setSavingAccount] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);
  const [savingPreferences, setSavingPreferences] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [accountSuccess, setAccountSuccess] = useState<string | null>(null);
  const [profileSuccess, setProfileSuccess] = useState<string | null>(null);
  const [preferencesSuccess, setPreferencesSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    const defaultOutput = i18n.t("preferences.defaultExpectedOutput");
    Promise.all([
      accountService.getAccount(accessToken),
      profileService.getProfile(accessToken),
      sessionService.getConsentStatus(accessToken),
    ])
      .then(([accountData, profileData, consent]) => {
        setAccount(accountData);
        setProfile(profileData);
        setConsentStatus(consent);
        setPreferences({
          ...emptyRecommendationDefaults(defaultOutput),
          seed_topics: profileData.recommendation_defaults?.seed_topics?.length
            ? profileData.recommendation_defaults.seed_topics
            : [...DEFAULT_SEED_TOPICS],
          expected_output:
            profileData.recommendation_defaults?.expected_output ?? defaultOutput,
          desired_depth: profileData.recommendation_defaults?.desired_depth ?? "medium",
          avoid_real_user_experiments:
            profileData.recommendation_defaults?.avoid_real_user_experiments ?? true,
        });
      })
      .catch(() => undefined)
      .finally(() => setLoading(false));
  }, [accessToken]);

  const setTab = (tab: ProfileTab) => {
    setSearchParams({ tab }, { replace: true });
  };

  const handleAccountSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!accessToken) {
      return;
    }

    setSavingAccount(true);
    setError(null);
    setAccountSuccess(null);

    try {
      const updated = await accountService.updateAccount(accessToken, {
        full_name: account.full_name?.trim(),
        email: account.email?.trim(),
        phone_number: account.phone_number?.trim(),
        whatsapp_opt_in: account.whatsapp_opt_in,
      });
      setAccount(updated);
      updateUser({
        fullName: updated.full_name,
        email: updated.email,
        phoneNumber: updated.phone_number ?? "",
        whatsappOptIn: updated.whatsapp_opt_in,
      });
      setAccountSuccess(t("profile.accountSaved"));
    } catch (err) {
      setError(err instanceof HttpError ? err.message : t("profile.errorSaveAccount"));
    } finally {
      setSavingAccount(false);
    }
  };

  const handleProfileSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!accessToken || !user || !profile.research_area?.trim()) {
      setError(t("profile.researchAreaRequired"));
      return;
    }

    setSavingProfile(true);
    setError(null);
    setProfileSuccess(null);

    const payload: UserProfile = {
      research_area: profile.research_area.trim(),
      academic_level: profile.academic_level,
      experience_with_ai: profile.experience_with_ai,
      experience_with_recommender_systems: profile.experience_with_recommender_systems,
      experience_with_scientific_writing: profile.experience_with_scientific_writing,
      goal_with_postrec: profile.goal_with_postrec?.trim(),
    };

    try {
      await profileService.updateProfile(accessToken, payload);
      let activeSessionId = sessionId;
      if (!activeSessionId) {
        const session = await sessionService.createSession(accessToken, user.userId);
        activeSessionId = session.session_id;
        setSessionId(activeSessionId);
      }
      await profileService.createSessionProfile(accessToken, {
        ...payload,
        user_id: user.userId,
        session_id: activeSessionId,
      });
      completeProfile();
      setProfileSuccess(t("profile.researchProfileSaved"));
    } catch (err) {
      setError(err instanceof HttpError ? err.message : t("profile.errorSaveProfile"));
    } finally {
      setSavingProfile(false);
    }
  };

  const handlePreferencesSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!accessToken) {
      return;
    }

    setSavingPreferences(true);
    setError(null);
    setPreferencesSuccess(null);

    try {
      const updated = await profileService.updateProfile(accessToken, {
        recommendation_defaults: preferences,
      });
      setProfile(updated);
      setPreferencesSuccess(t("profile.preferencesSaved"));
    } catch (err) {
      setError(err instanceof HttpError ? err.message : t("profile.errorSavePreferences"));
    } finally {
      setSavingPreferences(false);
    }
  };

  if (loading) {
    return <LoadingSpinner label={t("common.loadingProfile")} />;
  }

  const hasLearning =
    (profile.learned_topics?.length ?? 0) > 0 ||
    (profile.preferred_techniques?.length ?? 0) > 0 ||
    (profile.avoided_topics?.length ?? 0) > 0;

  return (
    <div className="page-shell">
      <PageHeader title={t("profile.title")} subtitle={t("profile.subtitle")} />

      {error ? <Alert variant="danger">{error}</Alert> : null}

      <Tab.Container activeKey={activeTab} onSelect={(key) => key && setTab(key as ProfileTab)}>
        <Card className="page-card profile-hub border-0">
          <Card.Header className="profile-hub__tabs px-2 pt-2 pb-0 border-0">
            <Nav variant="tabs" className="border-0">
              <Nav.Item>
                <Nav.Link eventKey="account">{t("profile.tabAccount")}</Nav.Link>
              </Nav.Item>
              <Nav.Item>
                <Nav.Link eventKey="research">{t("profile.tabResearch")}</Nav.Link>
              </Nav.Item>
              <Nav.Item>
                <Nav.Link eventKey="preferences">{t("profile.tabPreferences")}</Nav.Link>
              </Nav.Item>
              <Nav.Item>
                <Nav.Link eventKey="consent">{t("profile.tabConsent")}</Nav.Link>
              </Nav.Item>
            </Nav>
          </Card.Header>

          <Card.Body>
            <Tab.Content>
              <Tab.Pane eventKey="account">
                {accountSuccess ? <Alert variant="success">{accountSuccess}</Alert> : null}
                <div className="mb-4">
                  <LanguageSwitcher variant="inline" />
                </div>
                <Form onSubmit={handleAccountSubmit}>
                  <Row className="g-3 mb-3">
                    <Col md={6}>
                      <Form.Group>
                        <Form.Label>{t("profile.fullName")}</Form.Label>
                        <Form.Control
                          value={account.full_name ?? ""}
                          onChange={(e) => setAccount({ ...account, full_name: e.target.value })}
                          required
                        />
                      </Form.Group>
                    </Col>
                    <Col md={6}>
                      <Form.Group>
                        <Form.Label>{t("profile.email")}</Form.Label>
                        <Form.Control
                          type="email"
                          value={account.email ?? ""}
                          onChange={(e) => setAccount({ ...account, email: e.target.value })}
                          required
                        />
                      </Form.Group>
                    </Col>
                  </Row>

                  <Form.Group className="mb-3">
                    <Form.Label>{t("profile.whatsappNumber")}</Form.Label>
                    <Form.Control
                      type="tel"
                      value={account.phone_number ?? ""}
                      onChange={(e) => setAccount({ ...account, phone_number: e.target.value })}
                      placeholder={t("auth.whatsappPlaceholder")}
                      required
                    />
                    <Form.Text>{t("profile.whatsappHint")}</Form.Text>
                  </Form.Group>

                  <Form.Check
                    type="switch"
                    id="profile-whatsapp-opt-in"
                    className="mb-4"
                    label={t("profile.whatsappOptIn")}
                    checked={account.whatsapp_opt_in ?? false}
                    onChange={(e) => setAccount({ ...account, whatsapp_opt_in: e.target.checked })}
                  />

                  <Button type="submit" variant="primary" disabled={savingAccount}>
                    {savingAccount ? t("common.saving") : t("profile.saveAccount")}
                  </Button>
                </Form>
              </Tab.Pane>

              <Tab.Pane eventKey="research">
                {(profile.learned_topics?.length ?? 0) > 0 ? (
                  <Alert variant="info" className="small">
                    {t("profile.learnedTopicsHint", { count: profile.learned_topics?.length ?? 0 })}
                  </Alert>
                ) : null}
                {profileSuccess ? <Alert variant="success">{profileSuccess}</Alert> : null}

                <Form onSubmit={handleProfileSubmit}>
                  <Form.Group className="mb-3">
                    <Form.Label>{t("profile.researchArea")}</Form.Label>
                    <Form.Control
                      value={profile.research_area ?? ""}
                      onChange={(e) => setProfile({ ...profile, research_area: e.target.value })}
                      placeholder={t("profile.researchAreaPlaceholder")}
                      required
                    />
                  </Form.Group>

                  <Form.Group className="mb-3">
                    <Form.Label>{t("profile.academicLevel")}</Form.Label>
                    <Form.Select
                      value={profile.academic_level ?? "PhD"}
                      onChange={(e) => setProfile({ ...profile, academic_level: e.target.value })}
                    >
                      {ACADEMIC_LEVELS.map((level) => (
                        <option key={level} value={level}>
                          {academicLabel(level)}
                        </option>
                      ))}
                    </Form.Select>
                  </Form.Group>

                  <p className="fw-semibold mb-2">{t("profile.experience")}</p>
                  <Row className="g-3 mb-3">
                    <Col md={4}>
                      <Form.Label>{t("profile.experienceAi")}</Form.Label>
                      <Form.Select
                        value={profile.experience_with_ai ?? "Basic"}
                        onChange={(e) => setProfile({ ...profile, experience_with_ai: e.target.value })}
                      >
                        {EXPERIENCE_LEVELS.map((level) => (
                          <option key={level} value={level}>
                            {experienceLabel(level)}
                          </option>
                        ))}
                      </Form.Select>
                    </Col>
                    <Col md={4}>
                      <Form.Label>{t("profile.experienceRecsys")}</Form.Label>
                      <Form.Select
                        value={profile.experience_with_recommender_systems ?? "Basic"}
                        onChange={(e) =>
                          setProfile({ ...profile, experience_with_recommender_systems: e.target.value })
                        }
                      >
                        {EXPERIENCE_LEVELS.map((level) => (
                          <option key={level} value={level}>
                            {experienceLabel(level)}
                          </option>
                        ))}
                      </Form.Select>
                    </Col>
                    <Col md={4}>
                      <Form.Label>{t("profile.experienceWriting")}</Form.Label>
                      <Form.Select
                        value={profile.experience_with_scientific_writing ?? "Basic"}
                        onChange={(e) =>
                          setProfile({ ...profile, experience_with_scientific_writing: e.target.value })
                        }
                      >
                        {EXPERIENCE_LEVELS.map((level) => (
                          <option key={level} value={level}>
                            {experienceLabel(level)}
                          </option>
                        ))}
                      </Form.Select>
                    </Col>
                  </Row>

                  <Form.Group className="mb-4">
                    <Form.Label>{t("profile.goalLabel")}</Form.Label>
                    <Form.Control
                      as="textarea"
                      rows={3}
                      value={profile.goal_with_postrec ?? ""}
                      onChange={(e) => setProfile({ ...profile, goal_with_postrec: e.target.value })}
                      placeholder={t("profile.goalPlaceholder")}
                    />
                  </Form.Group>

                  <div className="d-flex gap-2 flex-wrap">
                    <Button type="submit" variant="primary" disabled={savingProfile}>
                      {savingProfile ? t("common.saving") : t("profile.saveResearchProfile")}
                    </Button>
                    <Button type="button" variant="outline-secondary" onClick={() => navigate("/runs/new")}>
                      {t("profile.startRun")}
                    </Button>
                  </div>
                </Form>
              </Tab.Pane>

              <Tab.Pane eventKey="preferences">
                <p className="text-secondary small mb-3">{t("profile.preferencesIntro")}</p>
                {preferencesSuccess ? <Alert variant="success">{preferencesSuccess}</Alert> : null}

                <RecommendationPreferencesForm
                  defaults={preferences}
                  onChange={setPreferences}
                  onSubmit={handlePreferencesSubmit}
                  submitting={savingPreferences}
                  submitLabel={t("profile.savePreferences")}
                />

                {hasLearning ? (
                  <div className="learning-summary mt-4 pt-3 border-top">
                    <p className="fw-semibold small mb-2">{t("profile.learnedFromReviews")}</p>
                    {(profile.preferred_techniques?.length ?? 0) > 0 ? (
                      <p className="small text-secondary mb-1">
                        <strong>{t("profile.preferredTechniques")}</strong>{" "}
                        {profile.preferred_techniques?.slice(0, 6).join(", ")}
                      </p>
                    ) : null}
                    {(profile.learned_topics?.length ?? 0) > 0 ? (
                      <p className="small text-secondary mb-1">
                        <strong>{t("profile.learnedTopics")}</strong>{" "}
                        {profile.learned_topics?.slice(0, 5).join(", ")}
                      </p>
                    ) : null}
                    {(profile.avoided_topics?.length ?? 0) > 0 ? (
                      <p className="small text-secondary mb-0">
                        <strong>{t("profile.avoidedTopics")}</strong>{" "}
                        {profile.avoided_topics?.slice(0, 5).join(", ")}
                      </p>
                    ) : null}
                  </div>
                ) : null}
              </Tab.Pane>

              <Tab.Pane eventKey="consent">
                <ConsentPanel status={consentStatus} readOnly />
              </Tab.Pane>
            </Tab.Content>
          </Card.Body>
        </Card>
      </Tab.Container>
    </div>
  );
}
