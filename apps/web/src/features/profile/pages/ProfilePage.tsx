import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { Button, Col, Form, Nav, Row, Tab } from "react-bootstrap";
import { useTranslation } from "react-i18next";
import { useNavigate, useSearchParams } from "react-router-dom";

import { ConsentPanel } from "@/features/consent/components/ConsentPanel";
import {
  emptyRecommendationDefaults,
  RecommendationPreferencesForm,
} from "@/features/profile/components/RecommendationPreferencesForm";
import { PageHeader } from "@/shared/ui/PageHeader";
import { InlineAlert } from "@/shared/ui/InlineAlert";
import { LanguageSwitcher } from "@/shared/ui/LanguageSwitcher";
import { LoadingSpinner } from "@/shared/ui/LoadingSpinner";
import { OnboardingProgress } from "@/shared/ui/OnboardingProgress";
import { NextStepBanner } from "@/shared/ui/NextStepBanner";
import { ACADEMIC_LEVELS, DEFAULT_SEED_TOPICS, EXPERIENCE_LEVELS } from "@/shared/constants";
import { useEnumLabel } from "@/shared/i18n/useEnumLabel";
import i18n from "@/shared/i18n";
import { useAuth } from "@/features/auth/context/AuthContext";
import { accountService, profileService, sessionService } from "@/shared/api";
import { getErrorMessage } from "@/shared/api/errors";
import type { RecommendationDefaults, UserAccount, UserConsentStatus, UserProfile } from "@/shared/types/api";

const TABS = ["account", "research", "preferences", "consent"] as const;
type ProfileTab = (typeof TABS)[number];

function isValidTab(value: string | null): value is ProfileTab {
  return TABS.includes(value as ProfileTab);
}

export function ProfilePage() {
  const { t } = useTranslation();
  const academicLabel = useEnumLabel("enums.academicLevel");
  const experienceLabel = useEnumLabel("enums.experience");
  const { accessToken, user, sessionId, setSessionId, completeProfile, updateUser, consentDone, profileDone } =
    useAuth();
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
          max_article_age_years:
            profileData.recommendation_defaults?.max_article_age_years ?? 5,
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
      setError(getErrorMessage(err, t("profile.errorSaveAccount")));
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

    const wasFirstProfileSave = !profileDone;

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
      if (wasFirstProfileSave) {
        navigate("/runs/new");
        return;
      }
      setProfileSuccess(t("profile.researchProfileSaved"));
    } catch (err) {
      setError(getErrorMessage(err, t("profile.errorSaveProfile")));
    } finally {
      setSavingProfile(false);
    }
  };

  const handlePreferencesSubmit = async (
    event: FormEvent,
    formDefaults: RecommendationDefaults,
  ) => {
    event.preventDefault();
    if (!accessToken) {
      return;
    }

    setSavingPreferences(true);
    setError(null);
    setPreferencesSuccess(null);

    try {
      const updated = await profileService.updateProfile(accessToken, {
        recommendation_defaults: formDefaults,
      });
      setProfile(updated);
      setPreferences(formDefaults);
      setPreferencesSuccess(t("profile.preferencesSaved"));
    } catch (err) {
      setError(getErrorMessage(err, t("profile.errorSavePreferences")));
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

  const setupIncomplete = !consentDone || !profileDone;

  return (
    <div className="page-shell">
      <div className="page-stack page-stack--tight">
        <PageHeader title={t("profile.title")} subtitle={t("profile.subtitle")} />

        {setupIncomplete ? (
          <div className="profile-setup panel">
            <OnboardingProgress />
            {!profileDone && activeTab === "research" ? (
              <p className="profile-setup__hint mb-0">{t("profile.researchSetupHint")}</p>
            ) : null}
          </div>
        ) : null}

        {error ? <InlineAlert variant="danger">{error}</InlineAlert> : null}

        {profileSuccess && profileDone && activeTab === "research" ? (
          <NextStepBanner
            title={t("conversion.profileReadyTitle")}
            description={t("conversion.profileReadyDesc")}
            ctaLabel={t("conversion.generateFirstRun")}
            ctaTo="/runs/new"
          />
        ) : profileSuccess ? (
          <InlineAlert variant="success">{profileSuccess}</InlineAlert>
        ) : null}

        <Tab.Container activeKey={activeTab} onSelect={(key) => key && setTab(key as ProfileTab)}>
          <div className="profile-hub panel">
            <div className="profile-hub__tabs" data-coach="coach-profile-tabs">
              <Nav variant="tabs" className="border-0">
                <Nav.Item>
                  <Nav.Link eventKey="account">{t("profile.tabAccount")}</Nav.Link>
                </Nav.Item>
                <Nav.Item>
                  <Nav.Link eventKey="research" data-coach="coach-profile-research-tab">
                    {t("profile.tabResearch")}
                  </Nav.Link>
                </Nav.Item>
                <Nav.Item>
                  <Nav.Link eventKey="preferences" data-coach="coach-profile-preferences-tab">
                    {t("profile.tabPreferences")}
                  </Nav.Link>
                </Nav.Item>
                <Nav.Item>
                  <Nav.Link eventKey="consent">{t("profile.tabConsent")}</Nav.Link>
                </Nav.Item>
              </Nav>
            </div>

            <div className="profile-hub__body">
              <Tab.Content>
              <Tab.Pane eventKey="account">
                {accountSuccess ? <InlineAlert variant="success">{accountSuccess}</InlineAlert> : null}
                <div className="mb-4">
                  <LanguageSwitcher variant="inline" />
                </div>
                <Form onSubmit={handleAccountSubmit} className="form-stack">
                  <Row className="g-3">
                    <Col md={6}>
                      <Form.Group className="field-group">
                        <Form.Label>{t("profile.fullName")}</Form.Label>
                        <Form.Control
                          value={account.full_name ?? ""}
                          onChange={(e) => setAccount({ ...account, full_name: e.target.value })}
                          required
                        />
                      </Form.Group>
                    </Col>
                    <Col md={6}>
                      <Form.Group className="field-group">
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

                  <Form.Group className="field-group">
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
                  <InlineAlert variant="info" className="small">
                    {t("profile.learnedTopicsHint", { count: profile.learned_topics?.length ?? 0 })}
                  </InlineAlert>
                ) : null}
                {profileSuccess && !profileDone ? <InlineAlert variant="success">{profileSuccess}</InlineAlert> : null}

                <Form onSubmit={handleProfileSubmit} className="form-stack">
                  <Form.Group className="field-group">
                    <Form.Label>{t("profile.researchArea")}</Form.Label>
                    <Form.Control
                      value={profile.research_area ?? ""}
                      onChange={(e) => setProfile({ ...profile, research_area: e.target.value })}
                      placeholder={t("profile.researchAreaPlaceholder")}
                      required
                    />
                  </Form.Group>

                  <Form.Group className="field-group">
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

                  <p className="profile-experience-heading">{t("profile.experience")}</p>
                  <Row className="g-3">
                    <Col md={4}>
                      <Form.Group className="field-group">
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
                      </Form.Group>
                    </Col>
                    <Col md={4}>
                      <Form.Group className="field-group">
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
                      </Form.Group>
                    </Col>
                    <Col md={4}>
                      <Form.Group className="field-group">
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
                      </Form.Group>
                    </Col>
                  </Row>

                  <Form.Group className="field-group">
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
                <div className="form-stack">
                <p className="profile-form-intro">{t("profile.preferencesIntro")}</p>
                {preferencesSuccess ? <InlineAlert variant="success">{preferencesSuccess}</InlineAlert> : null}

                <RecommendationPreferencesForm
                  defaults={preferences}
                  onChange={setPreferences}
                  onSubmit={handlePreferencesSubmit}
                  submitting={savingPreferences}
                  submitLabel={t("profile.savePreferences")}
                />

                {hasLearning ? (
                  <div className="learning-summary">
                    <p className="learning-summary__title">{t("profile.learnedFromReviews")}</p>
                    {(profile.preferred_techniques?.length ?? 0) > 0 ? (
                      <p className="mb-0">
                        <strong>{t("profile.preferredTechniques")}</strong>{" "}
                        {profile.preferred_techniques?.slice(0, 6).join(", ")}
                      </p>
                    ) : null}
                    {(profile.learned_topics?.length ?? 0) > 0 ? (
                      <p className="mb-0">
                        <strong>{t("profile.learnedTopics")}</strong>{" "}
                        {profile.learned_topics?.slice(0, 5).join(", ")}
                      </p>
                    ) : null}
                    {(profile.avoided_topics?.length ?? 0) > 0 ? (
                      <p className="mb-0">
                        <strong>{t("profile.avoidedTopics")}</strong>{" "}
                        {profile.avoided_topics?.slice(0, 5).join(", ")}
                      </p>
                    ) : null}
                  </div>
                ) : null}
                </div>
              </Tab.Pane>

              <Tab.Pane eventKey="consent">
                <ConsentPanel status={consentStatus} readOnly />
              </Tab.Pane>
            </Tab.Content>
            </div>
          </div>
        </Tab.Container>
      </div>
    </div>
  );
}
