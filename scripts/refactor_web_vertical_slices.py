"""Reorganize apps/web/src into vertical slices."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB_SRC = ROOT / "apps" / "web" / "src"

MOVES: list[tuple[str, str]] = [
    ("App.tsx", "app/App.tsx"),
    ("routes/AppRoutes.tsx", "app/routes.tsx"),
    ("pages/SignInPage.tsx", "features/auth/pages/SignInPage.tsx"),
    ("contexts/AuthContext.tsx", "features/auth/context/AuthContext.tsx"),
    ("services/auth/AuthService.ts", "features/auth/api/authService.ts"),
    ("pages/ConsentPage.tsx", "features/consent/pages/ConsentPage.tsx"),
    ("components/profile/ConsentPanel.tsx", "features/consent/components/ConsentPanel.tsx"),
    ("services/session/SessionService.ts", "features/session/api/sessionService.ts"),
    ("pages/ProfilePage.tsx", "features/profile/pages/ProfilePage.tsx"),
    ("components/profile/RecommendationPreferencesForm.tsx", "features/profile/components/RecommendationPreferencesForm.tsx"),
    ("services/profile/ProfileService.ts", "features/profile/api/profileService.ts"),
    ("services/account/AccountService.ts", "features/profile/api/accountService.ts"),
    ("utils/seedTopics.ts", "features/profile/utils/seedTopics.ts"),
    ("pages/RunsPage.tsx", "features/runs/pages/RunsPage.tsx"),
    ("pages/RunDetailPage.tsx", "features/runs/pages/RunDetailPage.tsx"),
    ("pages/NewRunPage.tsx", "features/runs/pages/NewRunPage.tsx"),
    ("contexts/RunsContext.tsx", "features/runs/context/RunsContext.tsx"),
    ("hooks/useRunDetail.ts", "features/runs/hooks/useRunDetail.ts"),
    ("services/runs/RunService.ts", "features/runs/api/runService.ts"),
    ("services/runs/runStream.ts", "features/runs/api/runStream.ts"),
    ("utils/recommendations.ts", "features/runs/utils/recommendations.ts"),
    ("utils/runLog.ts", "features/runs/utils/runLog.ts"),
    ("utils/formatCost.ts", "features/runs/utils/formatCost.ts"),
    ("utils/runs.ts", "features/runs/utils/runs.ts"),
    ("pages/SurveyPage.tsx", "features/survey/pages/SurveyPage.tsx"),
    ("pages/InsightsPage.tsx", "features/insights/pages/InsightsPage.tsx"),
    ("services/validation/ValidationService.ts", "features/insights/api/validationService.ts"),
    ("pages/TransparencyPage.tsx", "features/transparency/pages/TransparencyPage.tsx"),
    ("constants/transparencyModel.ts", "features/transparency/constants/transparencyModel.ts"),
    ("components/routing/ProtectedRoute.tsx", "features/routing/ProtectedRoute.tsx"),
    ("services/http/HttpClient.ts", "shared/api/httpClient.ts"),
    ("services/index.ts", "shared/api/index.ts"),
    ("hooks/useApiHealth.ts", "shared/hooks/useApiHealth.ts"),
    ("config/env.ts", "shared/config/env.ts"),
    ("types/api.ts", "shared/types/api.ts"),
    ("constants/index.ts", "shared/constants/index.ts"),
    ("components/layout", "shared/layout"),
    ("components/ui", "shared/ui"),
    ("i18n", "shared/i18n"),
    ("styles", "shared/styles"),
]

RUN_COMPONENTS = [
    "RecommendationDetail.tsx",
    "RecommendationViewer.tsx",
    "RefinementPanel.tsx",
    "RunUsagePanel.tsx",
    "RunListCard.tsx",
    "RunProgressPanel.tsx",
    "RunModeSelector.tsx",
    "IdeaCarousel.tsx",
    "EvidenceList.tsx",
    "SotaVerificationPanel.tsx",
]

TRANSPARENCY_COMPONENTS = [
    "MathBlock.tsx",
    "TransparencySection.tsx",
    "WeightTable.tsx",
]


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def move_paths() -> None:
    for src_rel, dst_rel in MOVES:
        src = WEB_SRC / src_rel
        dst = WEB_SRC / dst_rel
        if not src.exists():
            print(f"SKIP missing: {src_rel}")
            continue
        ensure_parent(dst)
        if dst.exists():
            print(f"SKIP exists: {dst_rel}")
            continue
        src.rename(dst)
        print(f"MOVED {src_rel} -> {dst_rel}")

    for name in RUN_COMPONENTS:
        src = WEB_SRC / "components" / "runs" / name
        dst = WEB_SRC / "features" / "runs" / "components" / name
        if src.exists() and not dst.exists():
            ensure_parent(dst)
            src.rename(dst)
            print(f"MOVED components/runs/{name} -> features/runs/components/{name}")

    for name in TRANSPARENCY_COMPONENTS:
        src = WEB_SRC / "components" / "transparency" / name
        dst = WEB_SRC / "features" / "transparency" / "components" / name
        if src.exists() and not dst.exists():
            ensure_parent(dst)
            src.rename(dst)
            print(f"MOVED components/transparency/{name} -> features/transparency/components/{name}")


IMPORT_REPLACEMENTS: list[tuple[str, str]] = [
    ('from "../services"', 'from "@/shared/api"'),
    ('from "../services/index"', 'from "@/shared/api"'),
    ('from "./services"', 'from "@/shared/api"'),
    ('from "../contexts/AuthContext"', 'from "@/features/auth/context/AuthContext"'),
    ('from "../contexts/RunsContext"', 'from "@/features/runs/context/RunsContext"'),
    ('from "../types/api"', 'from "@/shared/types/api"'),
    ('from "../../types/api"', 'from "@/shared/types/api"'),
    ('from "../constants"', 'from "@/shared/constants"'),
    ('from "../../constants"', 'from "@/shared/constants"'),
    ('from "../constants/index"', 'from "@/shared/constants"'),
    ('from "../config/env"', 'from "@/shared/config/env"'),
    ('from "../i18n"', 'from "@/shared/i18n"'),
    ('from "../hooks/useApiHealth"', 'from "@/shared/hooks/useApiHealth"'),
    ('from "../hooks/useRunDetail"', 'from "@/features/runs/hooks/useRunDetail"'),
    ('from "../components/layout/AppLayout"', 'from "@/shared/layout/AppLayout"'),
    ('from "../components/layout/AuthShell"', 'from "@/shared/layout/AuthShell"'),
    ('from "../components/layout/MobileBottomNav"', 'from "@/shared/layout/MobileBottomNav"'),
    ('from "../components/layout/SetupBanner"', 'from "@/shared/layout/SetupBanner"'),
    ('from "../components/ui/LoadingSpinner"', 'from "@/shared/ui/LoadingSpinner"'),
    ('from "../components/ui/PageHeader"', 'from "@/shared/ui/PageHeader"'),
    ('from "../components/ui/EmptyState"', 'from "@/shared/ui/EmptyState"'),
    ('from "../components/ui/OutcomeBadge"', 'from "@/shared/ui/OutcomeBadge"'),
    ('from "../components/ui/LanguageSwitcher"', 'from "@/shared/ui/LanguageSwitcher"'),
    ('from "../components/routing/ProtectedRoute"', 'from "@/features/routing/ProtectedRoute"'),
    ('from "../components/profile/RecommendationPreferencesForm"', 'from "@/features/profile/components/RecommendationPreferencesForm"'),
    ('from "../components/profile/ConsentPanel"', 'from "@/features/consent/components/ConsentPanel"'),
    ('from "../components/runs/', 'from "@/features/runs/components/'),
    ('from "../components/transparency/', 'from "@/features/transparency/components/'),
    ('from "../utils/seedTopics"', 'from "@/features/profile/utils/seedTopics"'),
    ('from "../utils/runs"', 'from "@/features/runs/utils/runs"'),
    ('from "../utils/recommendations"', 'from "@/features/runs/utils/recommendations"'),
    ('from "../utils/runLog"', 'from "@/features/runs/utils/runLog"'),
    ('from "../utils/formatCost"', 'from "@/features/runs/utils/formatCost"'),
    ('from "./http/HttpClient"', 'from "@/shared/api/httpClient"'),
    ('from "../http/HttpClient"', 'from "@/shared/api/httpClient"'),
    ('from "./auth/AuthService"', 'from "@/features/auth/api/authService"'),
    ('from "./account/AccountService"', 'from "@/features/profile/api/accountService"'),
    ('from "./profile/ProfileService"', 'from "@/features/profile/api/profileService"'),
    ('from "./runs/RunService"', 'from "@/features/runs/api/runService"'),
    ('from "./session/SessionService"', 'from "@/features/session/api/sessionService"'),
    ('from "./validation/ValidationService"', 'from "@/features/insights/api/validationService"'),
    ('from "../constants/transparencyModel"', 'from "@/features/transparency/constants/transparencyModel"'),
    ('from "../pages/ConsentPage"', 'from "@/features/consent/pages/ConsentPage"'),
    ('from "../pages/InsightsPage"', 'from "@/features/insights/pages/InsightsPage"'),
    ('from "../pages/NewRunPage"', 'from "@/features/runs/pages/NewRunPage"'),
    ('from "../pages/ProfilePage"', 'from "@/features/profile/pages/ProfilePage"'),
    ('from "../pages/RunDetailPage"', 'from "@/features/runs/pages/RunDetailPage"'),
    ('from "../pages/RunsPage"', 'from "@/features/runs/pages/RunsPage"'),
    ('from "../pages/SignInPage"', 'from "@/features/auth/pages/SignInPage"'),
    ('from "../pages/SurveyPage"', 'from "@/features/survey/pages/SurveyPage"'),
    ('from "../pages/TransparencyPage"', 'from "@/features/transparency/pages/TransparencyPage"'),
    ('from "./routes/AppRoutes"', 'from "@/app/routes"'),
    ('from "./App"', 'from "@/app/App"'),
    ('from "./AuthContext"', 'from "@/features/auth/context/AuthContext"'),
    ('from "./RunsContext"', 'from "@/features/runs/context/RunsContext"'),
    ('from "../services/runs/runStream"', 'from "@/features/runs/api/runStream"'),
    ('from "./runStream"', 'from "@/features/runs/api/runStream"'),
    ('from "./RunService"', 'from "@/features/runs/api/runService"'),
]


def rewrite_ts_files() -> int:
    changed = 0
    for path in WEB_SRC.rglob("*"):
        if path.suffix not in {".ts", ".tsx"}:
            continue
        text = path.read_text(encoding="utf-8")
        original = text
        for old, new in IMPORT_REPLACEMENTS:
            text = text.replace(old, new)
        if text != original:
            path.write_text(text, encoding="utf-8")
            changed += 1
    return changed


def update_main() -> None:
    main = WEB_SRC / "main.tsx"
    text = main.read_text(encoding="utf-8")
    text = text.replace('from "./App"', 'from "@/app/App"')
    text = text.replace('import "./styles/app.scss"', 'import "@/shared/styles/app.scss"')
    text = text.replace('import "./i18n"', 'import "@/shared/i18n"')
    main.write_text(text, encoding="utf-8")


def main() -> None:
    move_paths()
    changed = rewrite_ts_files()
    update_main()
    print(f"Updated imports in {changed} frontend files")


if __name__ == "__main__":
    main()
