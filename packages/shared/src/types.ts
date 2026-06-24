export type FileStatus = "uploading" | "complete" | "error";

export interface FileMetadata {
  key: string;
  filename: string;
  folder: string;
  size_bytes: number;
  size_human: string;
  content_type: string;
  uploaded_at: string;
  url: string | null;
}

export interface FileMetadataDetail {
  filename: string;
  size_bytes: number;
  size_human: string;
  mime_type: string;
  extension: string;
  md5: string;
  sha256: string;
  uploaded_at: string;
  // Image-specific
  image_width: number | null;
  image_height: number | null;
  exif: Record<string, string> | null;
  // PDF-specific
  pdf_pages: number | null;
  pdf_author: string | null;
  pdf_title: string | null;
  // Audio/Video
  duration_seconds: number | null;
  codec: string | null;
  bitrate: number | null;
}

export interface FileUploadResponse {
  key: string;
  filename: string;
  size_bytes: number;
  size_human: string;
  content_type: string;
  uploaded_at: string;
  url: string | null;
  metadata: FileMetadataDetail | null;
}

export interface DailyUploadCount {
  date: string;
  uploads: number;
}

export interface UploadStats {
  total_files: number;
  total_size_bytes: number;
  total_size_human: string;
  uploads_today: number;
  total_downloads: number;
}

// --- Prompt Showdown ---

export interface PromptVariant {
  name: string;
  template: string;
}

export interface ShowdownInput {
  label: string;
  vars: Record<string, string>;
}

export interface RunCell {
  variant: string;
  input_label: string;
  output: string;
  judge_score: number | null;
  judge_rationale: string | null;
  human_score: number | null;
}

export interface VariantScore {
  variant: string;
  avg_judge_score: number | null;
  avg_human_score: number | null;
  wins: number;
}

export interface ShowdownRun {
  run_id: string;
  title: string;
  created_at: string;
  gen_model: string;
  judge_model: string;
  judge_enabled: boolean;
  criteria: string;
  variants: PromptVariant[];
  inputs: ShowdownInput[];
  cells: RunCell[];
  leaderboard: VariantScore[];
}

export interface RunSummary {
  run_id: string;
  title: string;
  created_at: string;
  gen_model: string;
  variant_count: number;
  input_count: number;
  judge_enabled: boolean;
  best_variant: string | null;
  avg_judge_score: number | null;
}

export interface ShowdownStats {
  total_runs: number;
  total_variants_compared: number;
  avg_judge_score: number | null;
  best_variant: string | null;
}

export interface VariantWins {
  variant: string;
  wins: number;
}

export interface CreateRunRequest {
  title: string;
  variants: PromptVariant[];
  inputs: ShowdownInput[];
  gen_model?: string | null;
  judge_model?: string | null;
  judge_enabled: boolean;
  criteria: string;
}

export interface ScoreRequest {
  variant: string;
  input_label: string;
  human_score: number;
}
