"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ApiError,
  createRun,
  deleteFile,
  getFiles,
  getFileStats,
  getPreviewUrl,
  getRun,
  getRuns,
  getShowdownStats,
  getUploadActivity,
  getVariantWins,
  scoreCell,
} from "@/lib/api-client";
import type {
  CreateRunRequest,
  FileMetadata,
  ScoreRequest,
} from "@prompt-showdown/shared";

// Single source of truth for query keys. Keep these tightly scoped so that
// invalidating "files" doesn't blow away unrelated caches, and so an IDE
// "find usages" of `qk.files` reveals every consumer.
export const qk = {
  all: ["b2"] as const,
  files: (prefix?: string, limit?: number) =>
    [...qk.all, "files", prefix ?? "", limit ?? 100] as const,
  stats: () => [...qk.all, "stats"] as const,
  uploadActivity: (days: number) =>
    [...qk.all, "stats", "activity", days] as const,
  preview: (key: string) => [...qk.all, "preview", key] as const,
  // Showdown
  runs: () => [...qk.all, "runs"] as const,
  run: (id: string) => [...qk.all, "run", id] as const,
  showdownStats: () => [...qk.all, "showdown-stats"] as const,
  variantWins: () => [...qk.all, "variant-wins"] as const,
};

export function useFiles(prefix = "", limit = 100) {
  return useQuery<FileMetadata[], ApiError>({
    queryKey: qk.files(prefix, limit),
    queryFn: () => getFiles(prefix, limit),
  });
}

export function useFileStats() {
  return useQuery({
    queryKey: qk.stats(),
    queryFn: getFileStats,
  });
}

export function useUploadActivity(days = 7) {
  return useQuery({
    queryKey: qk.uploadActivity(days),
    queryFn: () => getUploadActivity(days),
  });
}

// Presigned preview URL — only fetched when `enabled` is true (e.g., when
// the dialog opens for a specific file). Kept short-lived (60s) because
// the URL itself has a presigned expiry and is cheap to regenerate.
export function usePreviewUrl(key: string | undefined, enabled: boolean) {
  return useQuery({
    queryKey: qk.preview(key ?? ""),
    queryFn: () => getPreviewUrl(key as string),
    enabled: enabled && !!key,
    staleTime: 60_000,
  });
}

export function useDeleteFile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (fileKey: string) => deleteFile(fileKey),
    // After delete, blow away every cached file list + stats. Cheap and
    // correct — the dashboard re-fetches lazily as components remount.
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.all });
    },
  });
}

// --- Prompt Showdown ---

export function useRuns() {
  return useQuery({ queryKey: qk.runs(), queryFn: getRuns });
}

export function useRun(runId: string | undefined) {
  return useQuery({
    queryKey: qk.run(runId ?? ""),
    queryFn: () => getRun(runId as string),
    enabled: !!runId,
  });
}

export function useShowdownStats() {
  return useQuery({ queryKey: qk.showdownStats(), queryFn: getShowdownStats });
}

export function useVariantWins() {
  return useQuery({ queryKey: qk.variantWins(), queryFn: getVariantWins });
}

export function useCreateRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (req: CreateRunRequest) => createRun(req),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.runs() });
      qc.invalidateQueries({ queryKey: qk.showdownStats() });
      qc.invalidateQueries({ queryKey: qk.variantWins() });
    },
  });
}

export function useScoreCell(runId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (req: ScoreRequest) => scoreCell(runId, req),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.run(runId) });
      qc.invalidateQueries({ queryKey: qk.runs() });
    },
  });
}
