<!-- last_verified: 2026-06-24 -->
# App Workflows

User journeys inside the application.

## Run a Showdown (primary journey)

- User navigates to `/showdowns/new`
- Defines N **prompt variants** (name + template with `{variable}` placeholders);
  detected variables are surfaced live
- Defines the **shared input set** (label + `key=value` variable fills per row)
- Picks the generation model (or accepts the default) and toggles the LLM judge
- Clicks **Run showdown** → `POST /runs` runs the variant×input grid through a
  Genblaze Pipeline (NVIDIA NIM), judges each output, and persists everything to
  Backblaze B2 under `showdowns/<run_id>/`
- On success: redirected to the run-detail grid
- See: [Showdown Runs](features/showdown-runs.md), [LLM Judge](features/llm-judge.md)

## Browse Run History and Score by Hand

- User navigates to `/showdowns` — the Run History list, scoped to the B2
  `showdowns/` prefix (the sample's own library), newest-first
- Opens a run → the N×M grid: variants as columns, inputs as rows
- Each cell shows the generated output, the judge score + rationale, and a 1–10
  human rating control
- Selecting a human rating writes the score back into the run record on B2 and
  refreshes the leaderboard
- **Export**: downloads the full run as a single JSON file
- See: [Run History](features/run-history.md)

## View Dashboard

- User navigates to `/` (home)
- Three parallel API calls load: showdown stats, wins-per-variant, recent runs
- Stat cards show: total runs, variants compared, average judge score, best variant
- Wins chart shows how often each variant won an input, across all runs
- Recent runs table links each row to its detail grid
- Empty state: "No runs yet" messaging
- See: [Dashboard](features/dashboard.md)

## Upload Files

- User navigates to `/upload`
- Drops or selects files in the dropzone
- Client validates file size (max 100MB) and type
- Progress bar shows per-file upload status
- On success: toast notification, green checkmark
- On failure: red status icon with error message
- User can clear completed uploads
- See: [File Upload](features/file-upload.md)

## Browse and Manage Files

- User navigates to `/files`
- Page loads file list from API (sorted most recent first)
- Files displayed in tree view with folders and type-specific icons
- Top-level folders auto-expand on load
- Hover a file row to see action buttons (preview / download / delete)
- **Preview**: opens dialog with image/PDF preview + metadata panel
- **Download**: fetches presigned URL, browser downloads file
- **Delete**: removes file from B2, row removed from tree, toast confirms
- Empty bucket shows "No files found" with upload prompt
- See: [File Browser](features/file-browser.md)

## View Dashboard

- User navigates to `/` (home)
- Three parallel API calls load: stats, recent files, upload activity
- Stats cards show: total files, storage used, uploads today, total downloads
- Upload chart shows last 7 days of upload activity as bar chart
- Recent uploads table shows last 10 files with filename, size, type, date
- Empty state: "No files uploaded yet" messages
- See: [Dashboard](features/dashboard.md)
