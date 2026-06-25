"""No-network signature-guard tests for the genblaze repo boundary.

These monkeypatch the genblaze SDK surfaces (Pipeline, NvidiaChatProvider, chat,
S3StorageBackend) so nothing hits the network, then assert our repo functions
call them with the arguments we expect. This protects the sample from silent
genblaze SDK drift (a renamed kwarg or changed call shape would fail here long
before a real run).
"""

import json
from typing import ClassVar

import pytest

from app.repo import genblaze_repo
from app.repo.genblaze_repo import JudgeVerdict


class _FakeResult:
    """Mimics a PipelineResult with one step whose asset carries chat text."""

    def __init__(self, text: str):
        asset = type("Asset", (), {"metadata": {"text": text}})()
        step = type("Step", (), {"assets": [asset]})()
        self.run = type("Run", (), {"steps": [step]})()


class _FakePipeline:
    """Records construction + .step() + .batch_run() calls for assertions."""

    calls: ClassVar[dict] = {}

    def __init__(self, name, *, max_concurrency=None, **kwargs):
        _FakePipeline.calls["name"] = name
        _FakePipeline.calls["max_concurrency"] = max_concurrency

    def step(self, provider, *, model, prompt, modality=None, **kwargs):
        _FakePipeline.calls["provider"] = type(provider).__name__
        _FakePipeline.calls["model"] = model
        _FakePipeline.calls["prompt"] = prompt
        _FakePipeline.calls["modality"] = modality
        return self

    def batch_run(self, input_rows, *, sink=None, **kwargs):
        _FakePipeline.calls["input_rows"] = input_rows
        _FakePipeline.calls["sink"] = sink
        return [_FakeResult(f"out-{i}") for i in range(len(input_rows))]


def test_run_variant_signature(monkeypatch):
    _FakePipeline.calls = {}

    provider_kwargs: dict = {}

    def _fake_provider(**kw):
        provider_kwargs.update(kw)
        return type("NvidiaChatProvider", (), {})()

    monkeypatch.setattr(genblaze_repo, "Pipeline", _FakePipeline)
    monkeypatch.setattr(genblaze_repo, "NvidiaChatProvider", _fake_provider)
    # Sentinel sink so we don't construct a real S3 backend / hit B2.
    monkeypatch.setattr(genblaze_repo, "_sink", lambda run_id: f"sink:{run_id}")

    rows = [{"q": "a"}, {"q": "b"}]
    outputs = genblaze_repo.run_variant(
        "run1", "concise", "Answer concisely: {q}", rows, "meta/llama-3.3-70b-instruct"
    )

    assert outputs == ["out-0", "out-1"]
    calls = _FakePipeline.calls
    assert calls["max_concurrency"] == genblaze_repo._MAX_CONCURRENCY
    assert calls["provider"] == "NvidiaChatProvider"
    assert calls["model"] == "meta/llama-3.3-70b-instruct"
    # prompt must be a PromptTemplate built from the variant template text
    assert isinstance(calls["prompt"], genblaze_repo.PromptTemplate)
    assert calls["prompt"].template == "Answer concisely: {q}"
    assert calls["modality"] == genblaze_repo.Modality.TEXT
    assert calls["input_rows"] == rows
    assert calls["sink"] == "sink:run1"
    # The provider must carry the configured per-request HTTP timeout (the 60s
    # genblaze default is too short for the 70B model on NIM's free tier).
    assert provider_kwargs["timeout"] == genblaze_repo.settings.showdown_request_timeout


def test_judge_cell_signature(monkeypatch):
    captured: dict = {}

    def _fake_chat(model, *, system=None, prompt=None, response_format=None, **kwargs):
        captured["model"] = model
        captured["system"] = system
        captured["prompt"] = prompt
        captured["response_format"] = response_format
        captured["kwargs"] = kwargs
        return type("ChatResponse", (), {"text": json.dumps({"score": 8, "rationale": "good"})})()

    monkeypatch.setattr(genblaze_repo, "chat", _fake_chat)

    verdict = genblaze_repo.judge_cell("the output", "be accurate", "meta/llama-3.3-70b-instruct")

    assert isinstance(verdict, JudgeVerdict)
    assert verdict.score == 8
    assert verdict.rationale == "good"
    assert captured["model"] == "meta/llama-3.3-70b-instruct"
    # The judge MUST request structured output via the Pydantic model.
    assert captured["response_format"] is JudgeVerdict
    assert "be accurate" in captured["prompt"]
    assert captured["kwargs"].get("temperature") == 0
    # The judge call must carry the configured per-request HTTP timeout.
    assert (
        captured["kwargs"].get("timeout")
        == genblaze_repo.settings.showdown_request_timeout
    )


def test_genblaze_imports_contained_in_repo():
    """Guard: genblaze must not be imported outside services/api/app/repo/."""
    import ast
    from pathlib import Path

    app_root = Path(__file__).parent.parent / "app"
    offenders = []
    for pyfile in app_root.rglob("*.py"):
        if "repo" in pyfile.relative_to(app_root).parts:
            continue
        tree = ast.parse(pyfile.read_text())
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods = [node.module]
            for m in mods:
                if m.startswith("genblaze"):
                    offenders.append(f"{pyfile.relative_to(app_root.parent)}: {m}")
    assert offenders == [], "genblaze imported outside repo/:\n" + "\n".join(offenders)


@pytest.mark.parametrize("text_field", ["text"])
def test_text_extraction_from_result(text_field):
    """_text_from_result reads the last asset's metadata['text']."""
    result = _FakeResult("hello")
    assert genblaze_repo._text_from_result(result) == "hello"
