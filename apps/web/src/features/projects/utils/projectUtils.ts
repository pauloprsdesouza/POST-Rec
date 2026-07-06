import type { ProjectPhase, ProjectTask, ResearchProject } from "@/shared/types/api";

export type PhaseVisualState = "done" | "current" | "upcoming";

export interface ProjectProgressStats {
  total: number;
  done: number;
  inProgress: number;
  skipped: number;
  pct: number;
}

export interface NextTaskRef {
  phase: ProjectPhase;
  task: ProjectTask;
  phaseIndex: number;
  taskIndex: number;
}

export function sortPhases(phases: ProjectPhase[]): ProjectPhase[] {
  return [...phases].sort((a, b) => a.order_index - b.order_index);
}

export function sortTasks(tasks: ProjectTask[]): ProjectTask[] {
  return [...tasks].sort((a, b) => a.order_index - b.order_index);
}

export function countPhaseTasks(phase: ProjectPhase): ProjectProgressStats {
  let total = 0;
  let done = 0;
  let inProgress = 0;
  let skipped = 0;

  for (const task of phase.tasks) {
    if (task.status === "skipped") {
      skipped += 1;
      continue;
    }
    total += 1;
    if (task.status === "done") {
      done += 1;
    } else if (task.status === "in_progress") {
      inProgress += 1;
    }
  }

  const pct = total > 0 ? Math.round((done / total) * 100) : 0;
  return { total, done, inProgress, skipped, pct };
}

export function countProjectProgress(project: ResearchProject): ProjectProgressStats {
  let total = 0;
  let done = 0;
  let inProgress = 0;
  let skipped = 0;

  for (const phase of project.phases) {
    const stats = countPhaseTasks(phase);
    total += stats.total;
    done += stats.done;
    inProgress += stats.inProgress;
    skipped += stats.skipped;
  }

  const pct = total > 0 ? Math.round((done / total) * 100) : project.progress_pct;
  return { total, done, inProgress, skipped, pct };
}

export function getPhaseVisualState(
  phase: ProjectPhase,
  currentPhaseId?: string | null,
): PhaseVisualState {
  const stats = countPhaseTasks(phase);
  if (stats.total > 0 && stats.done >= stats.total) {
    return "done";
  }
  if (phase.id === currentPhaseId) {
    return "current";
  }
  if (stats.done > 0 || stats.inProgress > 0) {
    return "current";
  }
  return "upcoming";
}

export function findNextTask(project: ResearchProject): NextTaskRef | null {
  const phases = sortPhases(project.phases);

  for (let phaseIndex = 0; phaseIndex < phases.length; phaseIndex += 1) {
    const phase = phases[phaseIndex];
    const tasks = sortTasks(phase.tasks);
    for (let taskIndex = 0; taskIndex < tasks.length; taskIndex += 1) {
      const task = tasks[taskIndex];
      if (task.status === "todo" || task.status === "in_progress") {
        return { phase, task, phaseIndex, taskIndex };
      }
    }
  }

  return null;
}

export function resolveActivePhaseId(
  project: ResearchProject,
  preferredPhaseId?: string | null,
): string | null {
  if (preferredPhaseId && project.phases.some((phase) => phase.id === preferredPhaseId)) {
    return preferredPhaseId;
  }
  if (project.current_phase_id) {
    return project.current_phase_id;
  }
  const next = findNextTask(project);
  if (next) {
    return next.phase.id;
  }
  return sortPhases(project.phases)[0]?.id ?? null;
}
