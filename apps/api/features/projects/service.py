"""Research project roadmap generation and persistence."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from apps.api.features.recommendations.llm import gemini_service
from apps.api.features.runs.access import ensure_run_access
from apps.api.shared.models import (
    ProjectPhase,
    ProjectTask,
    RecommendationCandidate,
    ResearchProject,
    User,
    UserResearchProfile,
)
from packages.postrec_core.prompts.project_roadmap import (
    PROJECT_ROADMAP_SYSTEM_PROMPT,
    PROJECT_ROADMAP_USER_TEMPLATE,
)

VALID_TASK_STATUSES = {"todo", "in_progress", "done", "skipped"}
VALID_PROJECT_STATUSES = {"active", "paused", "completed", "archived"}

DEFAULT_PHASES = [
    ("Foundation & literature", "Deepen your understanding of the gap and evidence base."),
    ("Study design", "Finalize methodology, datasets, and evaluation plan."),
    ("Execution", "Run experiments or implementations according to your plan."),
    ("Analysis & validation", "Interpret results, run ablations, and validate claims."),
    ("Writing", "Draft and refine the manuscript."),
    ("Publication", "Prepare submission materials and publish."),
]


def _format_evidence_papers(papers: list | None) -> str:
    if not papers:
        return "none"
    lines: list[str] = []
    for index, paper in enumerate(papers):
        if not isinstance(paper, dict):
            continue
        paper_id = paper.get("paper_id") or f"P{index + 1}"
        lines.append(f"[{paper_id}] {paper.get('title', 'Unknown')} ({paper.get('year', 'N/A')})")
    return "\n".join(lines) if lines else "none"


def _format_list(items: list | None) -> str:
    if not items:
        return "none"
    return ", ".join(str(item) for item in items)


def _fallback_roadmap(recommendation: RecommendationCandidate) -> dict[str, Any]:
    title = recommendation.title
    gap = recommendation.research_gap or "the identified research gap"
    method = recommendation.proposed_method or "your proposed method"
    plan = recommendation.experimental_plan or "the experimental plan"
    metrics = recommendation.evaluation_metrics or []
    datasets = recommendation.datasets or []
    risks = recommendation.risks or []
    paper_ids = [
        str(p.get("paper_id"))
        for p in (recommendation.evidence_papers or [])
        if isinstance(p, dict) and p.get("paper_id")
    ]

    phase_tasks: list[list[dict[str, Any]]] = [
        [
            {
                "title": "Read and annotate all evidence papers",
                "description": f"Review each paper cited for “{title}” and note methods, limitations, and how they relate to {gap}.",
                "guidance": "Strong literature grounding prevents rework later and strengthens your related-work section.",
                "effort": "M",
                "linked_fields": ["evidence_papers", "related_work_summary"],
                "linked_paper_ids": paper_ids[:5],
                "checklist": ["Skim abstracts", "Annotate key methods", "Note open questions"],
            },
            {
                "title": "Refine the research question",
                "description": f"Turn the gap into one focused question: {recommendation.research_question or gap}",
                "guidance": "A sharp question keeps scope manageable through execution and writing.",
                "effort": "S",
                "linked_fields": ["research_question", "research_gap"],
                "linked_paper_ids": [],
                "checklist": [],
            },
            {
                "title": "Draft a related-work outline",
                "description": "Organize prior work into themes that highlight what remains unsolved.",
                "guidance": "Use this outline as the backbone of your paper's related-work section.",
                "effort": "M",
                "linked_fields": ["related_work_summary"],
                "linked_paper_ids": paper_ids[:3],
                "checklist": [],
            },
            {
                "title": "Validate novelty against closest prior work",
                "description": "Explicitly compare your idea to the nearest papers and document your differentiation.",
                "guidance": "Early novelty checks reduce the risk of discovering overlap too late.",
                "effort": "M",
                "linked_fields": ["hypothesis", "expected_contribution"],
                "linked_paper_ids": paper_ids[:2],
                "checklist": [],
            },
        ],
        [
            {
                "title": "Finalize methodology",
                "description": f"Detail how you will implement: {method}",
                "guidance": "Write enough detail that a colleague could reproduce your approach.",
                "effort": "L",
                "linked_fields": ["proposed_method"],
                "linked_paper_ids": [],
                "checklist": ["Inputs/outputs defined", "Baselines chosen", "Assumptions listed"],
            },
            {
                "title": "Confirm datasets and access",
                "description": f"Verify availability and licenses for: {_format_list(datasets)}",
                "guidance": "Dataset access issues are a common blocker — resolve them before execution.",
                "effort": "M",
                "linked_fields": ["datasets"],
                "linked_paper_ids": [],
                "checklist": [],
            },
            {
                "title": "Define evaluation protocol",
                "description": f"Lock metrics and splits: {_format_list(metrics) if metrics else 'primary and secondary metrics'}",
                "guidance": "Pre-registering metrics reduces bias when interpreting results.",
                "effort": "M",
                "linked_fields": ["evaluation_metrics"],
                "linked_paper_ids": [],
                "checklist": [],
            },
            {
                "title": "Plan ethics and compliance",
                "description": "Check IRB, data privacy, or institutional requirements if human or sensitive data is involved.",
                "guidance": "Address compliance early to avoid delays before submission.",
                "effort": "S",
                "linked_fields": ["risks"],
                "linked_paper_ids": [],
                "checklist": [],
            },
        ],
        [
            {
                "title": "Set up reproducible environment",
                "description": "Create a repo or lab notebook with dependencies, seeds, and configuration documented.",
                "guidance": "Reproducibility supports both your own iteration and reviewer requests.",
                "effort": "M",
                "linked_fields": ["experimental_plan"],
                "linked_paper_ids": [],
                "checklist": [],
            },
            {
                "title": "Execute core experiments",
                "description": f"Follow the plan: {plan[:300]}{'…' if plan and len(plan) > 300 else ''}",
                "guidance": "Run the minimum viable experiment that tests your main hypothesis first.",
                "effort": "L",
                "linked_fields": ["experimental_plan", "hypothesis"],
                "linked_paper_ids": [],
                "checklist": ["Pilot run", "Full run", "Log failures"],
            },
            {
                "title": "Track risks and mitigations",
                "description": f"Monitor known risks: {_format_list(risks) if risks else 'technical and scope risks'}",
                "guidance": "Document how you handled unexpected issues — useful for limitations section.",
                "effort": "S",
                "linked_fields": ["risks"],
                "linked_paper_ids": [],
                "checklist": [],
            },
            {
                "title": "Checkpoint intermediate results",
                "description": "Save artifacts, figures, and notes at logical milestones during execution.",
                "guidance": "Checkpoints make analysis and writing much faster later.",
                "effort": "S",
                "linked_fields": ["experimental_plan"],
                "linked_paper_ids": [],
                "checklist": [],
            },
        ],
        [
            {
                "title": "Analyze primary results",
                "description": "Compute main metrics and compare against baselines defined in your design.",
                "guidance": "Start with the hypothesis your study was designed to test.",
                "effort": "L",
                "linked_fields": ["evaluation_metrics", "hypothesis"],
                "linked_paper_ids": [],
                "checklist": [],
            },
            {
                "title": "Run ablations or sensitivity checks",
                "description": "Test which components drive performance and how robust findings are.",
                "guidance": "Reviewers often ask for ablations — plan them proactively.",
                "effort": "M",
                "linked_fields": ["proposed_method"],
                "linked_paper_ids": [],
                "checklist": [],
            },
            {
                "title": "Validate claims against evidence",
                "description": "Ensure every claim in your story is supported by data or cited literature.",
                "guidance": "Aligns with Researchly's evidence-grounding philosophy.",
                "effort": "M",
                "linked_fields": ["expected_contribution", "evidence_papers"],
                "linked_paper_ids": paper_ids[:3],
                "checklist": [],
            },
            {
                "title": "Document limitations honestly",
                "description": "List scope limits, failure cases, and threats to validity.",
                "guidance": "Transparent limitations increase trust and speed up review.",
                "effort": "S",
                "linked_fields": ["risks"],
                "linked_paper_ids": [],
                "checklist": [],
            },
        ],
        [
            {
                "title": "Outline the manuscript",
                "description": "Map sections: intro, related work, method, experiments, results, conclusion.",
                "guidance": "Use your recommendation's contribution statement as the intro north star.",
                "effort": "M",
                "linked_fields": ["expected_contribution"],
                "linked_paper_ids": [],
                "checklist": [],
            },
            {
                "title": "Draft methods and experiments",
                "description": "Write reproducible method and experiment sections from your design notes.",
                "guidance": "Methods should match what you actually ran, not the initial plan.",
                "effort": "L",
                "linked_fields": ["proposed_method", "experimental_plan"],
                "linked_paper_ids": [],
                "checklist": [],
            },
            {
                "title": "Create figures and tables",
                "description": "Build publication-quality visuals for main results and comparisons.",
                "guidance": "Figures often drive first impressions — invest in clarity.",
                "effort": "M",
                "linked_fields": ["evaluation_metrics"],
                "linked_paper_ids": [],
                "checklist": [],
            },
            {
                "title": "Internal review pass",
                "description": "Share with a colleague or advisor for clarity, novelty, and missing citations.",
                "guidance": "Fresh eyes catch gaps you are too close to see.",
                "effort": "M",
                "linked_fields": ["related_work_summary"],
                "linked_paper_ids": [],
                "checklist": [],
            },
        ],
        [
            {
                "title": "Select target venue",
                "description": "Choose conferences or journals that fit scope, timeline, and contribution type.",
                "guidance": "Match venue expectations to your study design and result strength.",
                "effort": "S",
                "linked_fields": ["expected_contribution"],
                "linked_paper_ids": [],
                "checklist": ["Scope fit", "Deadline", "Open access policy"],
            },
            {
                "title": "Complete submission checklist",
                "description": "Formatting, anonymization, supplementary material, and metadata.",
                "guidance": "Use the venue's author guidelines as a literal checklist.",
                "effort": "M",
                "linked_fields": [],
                "linked_paper_ids": [],
                "checklist": ["Template applied", "References formatted", "Supplementary ready"],
            },
            {
                "title": "Submit and archive preprint (optional)",
                "description": "Upload to arXiv or institutional repository if appropriate for your field.",
                "guidance": "Preprints establish priority and invite early feedback.",
                "effort": "S",
                "linked_fields": [],
                "linked_paper_ids": [],
                "checklist": [],
            },
            {
                "title": "Plan revision strategy",
                "description": "Prepare for reviewer questions and a timeline for rebuttal or revision.",
                "guidance": "Anticipating reviewer concerns speeds up the revision cycle.",
                "effort": "S",
                "linked_fields": ["risks"],
                "linked_paper_ids": [],
                "checklist": [],
            },
        ],
    ]

    phases: list[dict[str, Any]] = []
    for index, (phase_title, phase_desc) in enumerate(DEFAULT_PHASES):
        phases.append(
            {
                "title": phase_title,
                "description": phase_desc,
                "tasks": phase_tasks[index],
            }
        )
    return {"phases": phases}


class ProjectService:
    def _get_recommendation_or_404(self, db: Session, recommendation_id: uuid.UUID) -> RecommendationCandidate:
        recommendation = db.query(RecommendationCandidate).filter_by(id=recommendation_id).first()
        if not recommendation:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        return recommendation

    def _ensure_project_access(self, project: ResearchProject, user: User) -> None:
        if project.user_id != user.id:
            raise HTTPException(status_code=403, detail="Not allowed to access this project")

    def _profile_context(self, db: Session, user: User) -> dict[str, str]:
        profile = db.query(UserResearchProfile).filter_by(user_id=user.id).first()
        return {
            "research_area": (profile.research_area if profile else None) or "General",
            "academic_level": (profile.academic_level if profile else None) or "unspecified",
            "writing_experience": (profile.experience_with_scientific_writing if profile else None) or "unspecified",
        }

    def generate_roadmap_payload(
        self,
        db: Session,
        *,
        run_id: uuid.UUID,
        recommendation: RecommendationCandidate,
        user: User,
        locale: str = "en-US",
    ) -> dict[str, Any]:
        profile = self._profile_context(db, user)
        prompt = PROJECT_ROADMAP_USER_TEMPLATE.format(
            research_area=profile["research_area"],
            academic_level=profile["academic_level"],
            writing_experience=profile["writing_experience"],
            locale=locale,
            title=recommendation.title,
            research_gap=recommendation.research_gap or "N/A",
            research_question=recommendation.research_question or "N/A",
            hypothesis=recommendation.hypothesis or "N/A",
            proposed_method=recommendation.proposed_method or "N/A",
            experimental_plan=recommendation.experimental_plan or "N/A",
            expected_contribution=recommendation.expected_contribution or "N/A",
            datasets=_format_list(recommendation.datasets),
            evaluation_metrics=_format_list(recommendation.evaluation_metrics),
            risks=_format_list(recommendation.risks),
            evidence_papers=_format_evidence_papers(recommendation.evidence_papers),
        )
        try:
            result = gemini_service._generate_json(
                db,
                str(run_id),
                operation="project_roadmap",
                system_prompt=PROJECT_ROADMAP_SYSTEM_PROMPT,
                user_prompt=prompt,
                temperature=0.4,
            )
        except Exception:
            return _fallback_roadmap(recommendation)
        phases = result.get("phases") if isinstance(result, dict) else None
        if not phases or not isinstance(phases, list):
            return _fallback_roadmap(recommendation)
        return result

    def _persist_roadmap(
        self,
        db: Session,
        *,
        project: ResearchProject,
        roadmap: dict[str, Any],
    ) -> ResearchProject:
        phases_data = roadmap.get("phases") or []
        first_phase_id: uuid.UUID | None = None

        for phase_index, phase_data in enumerate(phases_data):
            if not isinstance(phase_data, dict):
                continue
            phase = ProjectPhase(
                project_id=project.id,
                order_index=phase_index,
                title=str(phase_data.get("title") or f"Phase {phase_index + 1}"),
                description=phase_data.get("description"),
                status="in_progress" if phase_index == 0 else "todo",
            )
            db.add(phase)
            db.flush()
            if phase_index == 0:
                first_phase_id = phase.id

            tasks_data = phase_data.get("tasks") or []
            if not isinstance(tasks_data, list):
                tasks_data = []
            for task_index, task_data in enumerate(tasks_data):
                if not isinstance(task_data, dict):
                    continue
                db.add(
                    ProjectTask(
                        phase_id=phase.id,
                        order_index=task_index,
                        title=str(task_data.get("title") or f"Task {task_index + 1}"),
                        description=task_data.get("description"),
                        guidance=task_data.get("guidance"),
                        effort=task_data.get("effort"),
                        linked_fields=task_data.get("linked_fields"),
                        linked_paper_ids=task_data.get("linked_paper_ids"),
                        checklist=task_data.get("checklist"),
                        status="todo",
                    )
                )

        project.current_phase_id = first_phase_id
        project.progress_pct = 0
        db.commit()
        return self.get_project(db, project.id, project.user_id)

    def create_project(
        self,
        db: Session,
        *,
        user: User,
        recommendation_id: uuid.UUID,
        locale: str = "en-US",
    ) -> ResearchProject:
        recommendation = self._get_recommendation_or_404(db, recommendation_id)
        ensure_run_access(recommendation.run, user)

        existing = (
            db.query(ResearchProject)
            .filter_by(user_id=user.id, recommendation_id=recommendation_id)
            .options(joinedload(ResearchProject.phases).joinedload(ProjectPhase.tasks))
            .first()
        )
        if existing:
            return existing

        project = ResearchProject(
            user_id=user.id,
            run_id=recommendation.run_id,
            recommendation_id=recommendation.id,
            title=recommendation.title,
            status="active",
            locale=locale,
        )
        db.add(project)
        db.flush()

        roadmap = self.generate_roadmap_payload(
            db,
            run_id=recommendation.run_id,
            recommendation=recommendation,
            user=user,
            locale=locale,
        )
        return self._persist_roadmap(db, project=project, roadmap=roadmap)

    def list_projects(self, db: Session, user_id: uuid.UUID, limit: int = 50) -> list[ResearchProject]:
        return (
            db.query(ResearchProject)
            .filter_by(user_id=user_id)
            .options(joinedload(ResearchProject.phases))
            .order_by(ResearchProject.updated_at.desc())
            .limit(limit)
            .all()
        )

    def get_project(self, db: Session, project_id: uuid.UUID, user_id: uuid.UUID) -> ResearchProject:
        project = (
            db.query(ResearchProject)
            .filter_by(id=project_id, user_id=user_id)
            .options(joinedload(ResearchProject.phases).joinedload(ProjectPhase.tasks))
            .first()
        )
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project

    def get_project_by_recommendation(
        self, db: Session, user_id: uuid.UUID, recommendation_id: uuid.UUID
    ) -> ResearchProject | None:
        return (
            db.query(ResearchProject)
            .filter_by(user_id=user_id, recommendation_id=recommendation_id)
            .options(joinedload(ResearchProject.phases).joinedload(ProjectPhase.tasks))
            .first()
        )

    def _recompute_progress(self, db: Session, project: ResearchProject) -> None:
        phases = (
            db.query(ProjectPhase)
            .filter_by(project_id=project.id)
            .options(joinedload(ProjectPhase.tasks))
            .order_by(ProjectPhase.order_index)
            .all()
        )
        total = 0
        done = 0
        current_phase_id: uuid.UUID | None = None

        for phase in phases:
            phase_tasks = phase.tasks or []
            active_in_phase = False
            phase_done = True
            for task in phase_tasks:
                if task.status == "skipped":
                    continue
                total += 1
                if task.status == "done":
                    done += 1
                else:
                    phase_done = False
                    if current_phase_id is None and task.status in {"todo", "in_progress"}:
                        current_phase_id = phase.id
                    if task.status in {"todo", "in_progress"}:
                        active_in_phase = True

            if active_in_phase and phase.status != "done":
                phase.status = "in_progress"
            elif phase_done and phase_tasks:
                phase.status = "done"
            elif phase.status == "done" and not phase_done:
                phase.status = "in_progress"

        if current_phase_id is None and phases:
            for phase in reversed(phases):
                if any(t.status != "skipped" for t in (phase.tasks or [])):
                    current_phase_id = phase.id
                    break

        project.progress_pct = round(100 * done / total) if total else 0
        project.current_phase_id = current_phase_id
        if total > 0 and done >= total:
            project.status = "completed"
        elif project.status == "completed" and done < total:
            project.status = "active"

    def update_task(
        self,
        db: Session,
        *,
        user: User,
        project_id: uuid.UUID,
        task_id: uuid.UUID,
        status: str | None = None,
        user_notes: str | None = None,
    ) -> ProjectTask:
        project = self.get_project(db, project_id, user.id)
        task = (
            db.query(ProjectTask)
            .join(ProjectPhase, ProjectPhase.id == ProjectTask.phase_id)
            .filter(ProjectTask.id == task_id, ProjectPhase.project_id == project.id)
            .first()
        )
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if status is not None:
            if status not in VALID_TASK_STATUSES:
                raise HTTPException(status_code=400, detail="Invalid task status")
            task.status = status
            task.completed_at = datetime.now(timezone.utc) if status == "done" else None

        if user_notes is not None:
            task.user_notes = user_notes

        self._recompute_progress(db, project)
        db.commit()
        db.refresh(task)
        return task

    def export_markdown(self, project: ResearchProject) -> str:
        lines = [
            f"# {project.title}",
            "",
            f"Progress: {project.progress_pct}%",
            "",
            "> Guidance only — adapt to your institution, advisor, and field requirements.",
            "",
        ]
        for phase in sorted(project.phases, key=lambda item: item.order_index):
            lines.append(f"## {phase.title}")
            if phase.description:
                lines.append(phase.description)
            lines.append("")
            for task in sorted(phase.tasks, key=lambda item: item.order_index):
                checkbox = "x" if task.status == "done" else " "
                lines.append(f"- [{checkbox}] **{task.title}** ({task.status})")
                if task.description:
                    lines.append(f"  - {task.description}")
                if task.guidance:
                    lines.append(f"  - *Why:* {task.guidance}")
                if task.checklist:
                    for item in task.checklist:
                        lines.append(f"    - [ ] {item}")
                if task.user_notes:
                    lines.append(f"  - Notes: {task.user_notes}")
                lines.append("")
        return "\n".join(lines).strip() + "\n"

    def project_to_dict(self, project: ResearchProject, *, include_phases: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": str(project.id),
            "run_id": str(project.run_id),
            "recommendation_id": str(project.recommendation_id),
            "title": project.title,
            "status": project.status,
            "progress_pct": project.progress_pct,
            "current_phase_id": str(project.current_phase_id) if project.current_phase_id else None,
            "locale": project.locale,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        }
        if not include_phases:
            return payload

        phases_payload: list[dict[str, Any]] = []
        for phase in sorted(project.phases, key=lambda item: item.order_index):
            tasks_payload = [
                {
                    "id": str(task.id),
                    "order_index": task.order_index,
                    "title": task.title,
                    "description": task.description,
                    "guidance": task.guidance,
                    "effort": task.effort,
                    "linked_fields": task.linked_fields or [],
                    "linked_paper_ids": task.linked_paper_ids or [],
                    "checklist": task.checklist or [],
                    "status": task.status,
                    "user_notes": task.user_notes,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                }
                for task in sorted(phase.tasks, key=lambda item: item.order_index)
            ]
            phases_payload.append(
                {
                    "id": str(phase.id),
                    "order_index": phase.order_index,
                    "title": phase.title,
                    "description": phase.description,
                    "status": phase.status,
                    "tasks": tasks_payload,
                }
            )
        payload["phases"] = phases_payload
        return payload


project_service = ProjectService()
