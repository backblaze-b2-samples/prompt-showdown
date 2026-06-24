// Small client-side helpers for the New Showdown form.

/** Extract {variable} placeholder names from a template string. */
export function extractVars(template: string): string[] {
  const matches = template.matchAll(/\{([a-zA-Z_][a-zA-Z0-9_]*)\}/g);
  return Array.from(matches, (m) => m[1]);
}

/** Parse "key=value" lines into a flat record. Blank lines are ignored. */
export function parseVars(text: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const line of text.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    const eq = trimmed.indexOf("=");
    if (eq === -1) continue;
    const key = trimmed.slice(0, eq).trim();
    const value = trimmed.slice(eq + 1).trim();
    if (key) out[key] = value;
  }
  return out;
}
