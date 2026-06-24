"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Trash2, Swords } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCreateRun } from "@/lib/queries";
import { extractVars, parseVars } from "@/lib/showdown";

interface VariantDraft {
  name: string;
  template: string;
}
interface InputDraft {
  label: string;
  varsText: string; // "key=value" lines
}

const DEFAULT_GEN_MODEL = "meta/llama-3.3-70b-instruct";

export function NewShowdownForm() {
  const router = useRouter();
  const createRun = useCreateRun();

  const [title, setTitle] = useState("");
  const [genModel, setGenModel] = useState("");
  const [judgeEnabled, setJudgeEnabled] = useState(true);
  const [criteria, setCriteria] = useState(
    "Accuracy, relevance, and clarity of the response.",
  );
  const [variants, setVariants] = useState<VariantDraft[]>([
    { name: "concise", template: "Answer concisely: {question}" },
    { name: "detailed", template: "Give a thorough, well-structured answer to: {question}" },
  ]);
  const [inputs, setInputs] = useState<InputDraft[]>([
    { label: "geography", varsText: "question=What is the capital of France?" },
    { label: "science", varsText: "question=Why is the sky blue?" },
  ]);

  // Surface the template variables so users know which keys to fill per input.
  const detectedVars = useMemo(
    () => Array.from(new Set(variants.flatMap((v) => extractVars(v.template)))),
    [variants],
  );

  const updateVariant = (i: number, patch: Partial<VariantDraft>) =>
    setVariants((vs) => vs.map((v, idx) => (idx === i ? { ...v, ...patch } : v)));
  const updateInput = (i: number, patch: Partial<InputDraft>) =>
    setInputs((rows) => rows.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));

  async function handleSubmit() {
    if (!title.trim()) return toast.error("Give the showdown a title.");
    if (variants.some((v) => !v.name.trim() || !v.template.trim()))
      return toast.error("Every variant needs a name and template.");
    if (inputs.some((r) => !r.label.trim()))
      return toast.error("Every input row needs a label.");

    try {
      const run = await createRun.mutateAsync({
        title: title.trim(),
        gen_model: genModel.trim() || null,
        judge_enabled: judgeEnabled,
        criteria: criteria.trim(),
        variants: variants.map((v) => ({ name: v.name.trim(), template: v.template })),
        inputs: inputs.map((r) => ({ label: r.label.trim(), vars: parseVars(r.varsText) })),
      });
      toast.success("Showdown complete — outputs preserved on B2.");
      router.push(`/showdowns/${run.run_id}`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Showdown run failed.");
    }
  }

  return (
    <div className="space-y-8 max-w-4xl">
      <div className="animate-fade-in border-b border-border pb-5">
        <h1 className="page-title">New Showdown</h1>
        <p className="text-sm text-muted-foreground mt-1.5">
          Define prompt variants and a shared input set. Each cell is generated
          via NVIDIA NIM (through Genblaze) and preserved on Backblaze B2.
        </p>
      </div>

      <Card>
        <CardHeader className="border-b border-border py-4 px-5">
          <CardTitle className="card-title">Run settings</CardTitle>
        </CardHeader>
        <CardContent className="p-5 space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Customer support tone v1 vs v2"
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="model">Generation model</Label>
              <Input
                id="model"
                value={genModel}
                onChange={(e) => setGenModel(e.target.value)}
                placeholder={DEFAULT_GEN_MODEL}
              />
            </div>
            <div className="space-y-1.5">
              <Label className="block">LLM judge</Label>
              <div className="flex items-center gap-2 h-9">
                <Switch checked={judgeEnabled} onCheckedChange={setJudgeEnabled} />
                <span className="text-sm text-muted-foreground">
                  {judgeEnabled ? "Score every output" : "Generation only"}
                </span>
              </div>
            </div>
          </div>
          {judgeEnabled && (
            <div className="space-y-1.5">
              <Label htmlFor="criteria">Judging criteria</Label>
              <Textarea
                id="criteria"
                value={criteria}
                onChange={(e) => setCriteria(e.target.value)}
                rows={2}
              />
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="border-b border-border py-4 px-5 flex flex-row items-center justify-between">
          <CardTitle className="card-title">Prompt variants</CardTitle>
          <Button
            size="sm"
            variant="outline"
            className="h-7"
            onClick={() => setVariants((vs) => [...vs, { name: "", template: "" }])}
          >
            <Plus className="h-3.5 w-3.5" /> Add variant
          </Button>
        </CardHeader>
        <CardContent className="p-5 space-y-4">
          {variants.map((v, i) => (
            <div key={i} className="rounded-lg border border-border p-3 space-y-2">
              <div className="flex items-center gap-2">
                <Input
                  value={v.name}
                  onChange={(e) => updateVariant(i, { name: e.target.value })}
                  placeholder="variant name"
                  className="max-w-xs"
                />
                {variants.length > 1 && (
                  <Button
                    size="icon"
                    variant="ghost"
                    className="h-8 w-8 ml-auto"
                    onClick={() => setVariants((vs) => vs.filter((_, idx) => idx !== i))}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </div>
              <Textarea
                value={v.template}
                onChange={(e) => updateVariant(i, { template: e.target.value })}
                placeholder="Prompt template — use {variable} placeholders"
                rows={3}
                className="font-mono text-sm"
              />
            </div>
          ))}
          {detectedVars.length > 0 && (
            <p className="text-xs text-muted-foreground">
              Template variables detected:{" "}
              {detectedVars.map((vn) => (
                <code key={vn} className="font-mono mr-1">
                  {`{${vn}}`}
                </code>
              ))}
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="border-b border-border py-4 px-5 flex flex-row items-center justify-between">
          <CardTitle className="card-title">Shared input set</CardTitle>
          <Button
            size="sm"
            variant="outline"
            className="h-7"
            onClick={() => setInputs((rows) => [...rows, { label: "", varsText: "" }])}
          >
            <Plus className="h-3.5 w-3.5" /> Add input
          </Button>
        </CardHeader>
        <CardContent className="p-5 space-y-4">
          {inputs.map((r, i) => (
            <div key={i} className="rounded-lg border border-border p-3 space-y-2">
              <div className="flex items-center gap-2">
                <Input
                  value={r.label}
                  onChange={(e) => updateInput(i, { label: e.target.value })}
                  placeholder="input label"
                  className="max-w-xs"
                />
                {inputs.length > 1 && (
                  <Button
                    size="icon"
                    variant="ghost"
                    className="h-8 w-8 ml-auto"
                    onClick={() => setInputs((rows) => rows.filter((_, idx) => idx !== i))}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </div>
              <Textarea
                value={r.varsText}
                onChange={(e) => updateInput(i, { varsText: e.target.value })}
                placeholder={"key=value (one per line)\nquestion=What is the capital of France?"}
                rows={2}
                className="font-mono text-sm"
              />
            </div>
          ))}
        </CardContent>
      </Card>

      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={() => router.push("/showdowns")}>
          Cancel
        </Button>
        <Button onClick={handleSubmit} disabled={createRun.isPending}>
          <Swords className="h-4 w-4" />
          {createRun.isPending ? "Running…" : "Run showdown"}
        </Button>
      </div>
    </div>
  );
}
