# Local LLMs for Long-Context Meeting Summarization

**Date:** 2026-08-24
**Context:** Scoping the local-LLM variant of `notebooks/SummaryPromptVariations.ipynb`
(`SummaryPromptVariations_LocalLLM.ipynb`). We run a llama.cpp `llama-server`
(OpenAI-compatible endpoint) locally on an **RTX A5500 Laptop GPU, 16 GB VRAM**.
Goal: replace the Anthropic summarizer with a local model that can handle long
meeting transcripts *decently*. This doc captures the web/forum research behind
that decision.

> Source-quality note: much of the 2026 "best local LLM" web content is
> SEO/AI-generated listicle material — treat exact specs (variant sizes, release
> dates, VRAM figures) as **verify-on-download**. The trustworthy signals here are
> the **RULER benchmark** results and **Hacker News practitioner threads**;
> r/LocalLLaMA was not directly fetchable (crawler-blocked) but its consensus is
> echoed on HN. Vendor/blog spec pages are the least reliable.

---

## TL;DR / decisions

1. **Advertised context ≠ usable context.** Models claim 128K–256K but degrade
   well before that. Plan for **~32k *effective* tokens** on 16 GB hardware,
   regardless of the model's advertised window.
2. **Meeting transcripts are a worst case** for long context (multi-speaker,
   middle-heavy, topic shifts) — "lost-in-the-middle" hits exactly where the
   substance lives.
3. **On 16 GB, the practical sweet spot is the 8B–14B class** at Q4, context
   capped ~32k. Qwen family currently leads on long-context *retention*.
4. **Build map-reduce / hierarchical merge for real** (not a stub). It's the
   community- *and* research-endorsed answer for anything longer than the
   effective window. This flipped our earlier "stub it" plan.

---

## The core finding: advertised vs. effective context

Advertised context capacity and effective long-context robustness are **distinct
properties**. Most models peak at short context (~4k) and degrade as sequences grow.

### RULER benchmark (4k → 32k accuracy)

| Model            | 4k     | 32k    | Notes                                  |
|------------------|--------|--------|----------------------------------------|
| **Qwen3-8B**     | 94.8%  | 91.0%  | Unusually stable — best-in-class retention |
| Qwen3-4B         | high   | strong | Also strong for its size               |
| **Gemma 3 12B**  | 94.7%  | 80.4%  | Good short-context, pronounced falloff |
| Gemma 3 4B       | 90.9%  | 62.3%  | Steep degradation — avoid for long docs |

**Takeaway:** the Qwen3 family retains long-context accuracy notably better than
Gemma 3 at the same size. For summarizing long transcripts, retention > raw
window size.

### "Lost-in-the-middle"

LLMs reliably recall the **start and end** of the window but miss the
**~40k–80k token middle** on long inputs. A big advertised window does not mean
reliable recall across it — and a meeting's real content sits in that middle.

---

## Models that actually fit 16 GB VRAM (Q4)

| Model              | Advertised | Practical (16 GB) | ~VRAM @32k | Verdict |
|--------------------|-----------|-------------------|------------|---------|
| **Qwen2.5-7B** (current) | 32K   | ~32k              | ~5.4 GB (measured) | Fine for first tests; lots of headroom |
| **Qwen3-8B**       | 128K      | ~32k reliable     | ~8–9 GB    | Community "champ" for 16 GB; safest upgrade |
| **Qwen3-14B**      | 128K      | ~32k (cap it)     | ~12 GB     | Great quality @32k; **128k ≈ 18 GB → over 16 GB** |
| **Gemma 3 12B**    | 128K      | ~32k              | ~12 GB     | Weaker long-context retention (RULER) |
| **Gemma 4 12B**    | 256K      | see below         | ~12 GB int8 | Newest; verify runnable quant |

> Ollama/llama.cpp note: **explicitly set the context size** (`num_ctx` /
> `-c`) — runtimes don't auto-enable the full window, and oversizing it wastes
> VRAM on KV cache.

### On 16 GB, VRAM is *not* the binding constraint at 7B/32k

Our measured startup: ~5.4 GiB used with the full 32k window (KV cache ~950 MiB),
leaving ~9.8 GiB free. **The 32k context window itself is the limiter, not
memory** — which is exactly why chunking (not a bigger KV cache) is the right
lever.

---

## Gemma 4 (specifically requested)

Newest generation, genuinely interesting, but read the marketing skeptically:

- **Advertised 256K context**, pitched as "runs on a 16 GB laptop."
- **HN pushback:** 12B at int8 ≈ 12 GB, leaving almost no OS/KV headroom on
  16 GB. You'd want a **Q4 / QAT quant** to run it comfortably; full-precision
  benchmarks aren't what you'd actually run. bf16 weights ≈ 24 GB.
- Reported ~5 tok/s on a 12 GB RTX 3060 (CPU offload); native GPU should be 20+.
- **Strong benchmarks** (beats Gemma 3 27B on reasoning at ~half the RAM;
  MMLU-Pro ~77%). **Native audio input** — a possible future angle: summarize
  meeting *audio* directly, skipping Whisper.
- **Sentiment:** HN still leans "**Qwen is the 16 GB champ; Gemma good for
  general tasks**." Qwen reportedly "holds up well even at low quants (Q3–Q4)."
- Spec details are **inconsistent across sources** (variant sizes cited as
  12B / 26B / 31B; multiple release dates) — verify on download.

---

## What the summarization research says

Independent of model choice, the meeting-summarization literature converges on
**segmentation + hierarchical merge**:

- Directly processing large multi-speaker dialogue chunks causes **hallucination
  even in strong LLMs**.
- **Segment transcripts into topically focused chunks**, summarize each (map),
  then summarize the summaries (reduce / hierarchical merge). This reduces
  hallucination and improves topic coherence.
- RAG is an alternative for cost-effective long-context summarization, but
  map-reduce is simpler and sufficient here.

**Implication:** the map-reduce path in the notebook should be **fully
implemented**, defaulting to single-shot and auto-falling-back to chunked when a
token-budget check says the input exceeds the effective window (~32k).

---

## Recommended experiment ladder (matches limited bandwidth)

1. **Qwen2.5-7B** (already running) — validate prompt kinds end-to-end; fine to ~32k.
2. **Qwen3-8B** — low-risk quality bump, comfortable on 16 GB.
3. **A/B (optional):** **Qwen3-14B** (cap context at 32k) or **Gemma 4 12B (Q4)**.

The notebook's local wrapper is just the OpenAI-compatible endpoint, so **only
the loaded GGUF changes** across all of these — no code changes to swap models.

---

## Sources

- [Long Context Local LLMs (2026): 128K Models You Can Run Now — promptquorum](https://www.promptquorum.com/local-llms/long-context-local-llms)
- [Gemma 4 12B: Best Local LLM for 16GB RAM — ModelFit](https://modelfit.io/blog/gemma-4-12b-local-llm-16gb/)
- [Gemma 4 12B guide — buildfastwithai](https://www.buildfastwithai.com/blogs/gemma-4-12b-guide)
- [HN: Gemma 4 12B — a unified, encoder-free multimodal model](https://news.ycombinator.com/item?id=48385906)
- [HN: Qwen 3.8 27B / Gemma 4 comparison](https://news.ycombinator.com/item?id=49305335)
- [HN: Running local models on an M4 with 24GB memory](https://news.ycombinator.com/item?id=48089091)
- [Segment-level Tree Search for Long Meeting Document Summarization (arXiv)](https://arxiv.org/pdf/2606.08445)
- [Context-Aware Hierarchical Merging for Long Document Summarization (arXiv)](https://arxiv.org/pdf/2502.00977)
- [Action-Item-Driven Summarization of Long Meeting Transcripts (arXiv)](https://arxiv.org/pdf/2312.17581)
- RULER benchmark long-context degradation figures (as reported across the above 2026 comparison write-ups)
