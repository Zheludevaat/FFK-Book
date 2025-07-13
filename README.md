# FFK-Book

## Introduction

FFK-Book demonstrates a cloud-centric workflow for writing a long-form book using cooperating OpenAI agents. Research, drafting, reviewing, and updates are handled through a scripted pipeline so that every section remains stylistically consistent while facts stay current.

This repository shows how a minimal set of Python scripts can coordinate multiple GPT‑4.1 agents to produce a complete manuscript. After filling out the chapter outline and voice rules, you simply run `python run_pipeline.py` to start generating drafts. Each run stores research notes, prompts, and Markdown output under version control, making it easy to review changes and iterate.
The repository's main purpose is to show how a small set of agent scripts can build a manuscript end to end. Edit the outline and style files, provide an API key, and run one command to start generating chapters automatically. Every generated draft appears under `drafts/` for you to inspect and refine.
Supporting documents in `docs/` describe the style guide, QA checklist, and the detailed chapter plan used by the automation.
This repository offers a repeatable process: fill in `config/outline.yaml`, tweak the style guide, provide your API key, and run the pipeline to generate drafts automatically.

At a high level, you prepare a YAML outline listing each chapter and its short closing story, adjust the tone rules in `config/style.md`, then launch `python run_pipeline.py`. The agents research and draft each part in sequence, saving Markdown files under `drafts/` for you to review and edit. Because every step persists to plain text, you can track and improve the manuscript over time without losing context.

The primary goal of this project is to showcase how cooperating GPT-4.1 agents can draft and refine a book automatically. By combining research, drafting, and review in a single script, authors keep creative control while repetitive steps run in the cloud. All data is stored in text files so progress stays transparent in version control.

This project serves as a working template for orchestrating multiple GPT‑4.1 agents to craft a coherent manuscript. By editing a simple YAML outline and style file, you can trigger a fully automated cycle of research, prompt creation, drafting, and review. Each run deposits new material into `drafts/` so you can track progress in version control.

The repository's goal is to showcase how a lightweight Python harness can coordinate different GPT‑4.1 models to produce an entire manuscript with minimal manual intervention. By running the included pipeline you can generate draft chapters, review diffs, and gradually build a polished book while keeping all configuration in simple text files. The active style rules for each agent are read from `config/style.md`; an expanded reference lives at `docs/style-guide.md` for human editors.

In short, you edit the outline and style files, provide your API key, and let `run_pipeline.py` orchestrate research, drafting, review, and updates. Each run appends new material to `drafts/` while logging sources and diffs for transparency.

This setup aims to make book generation nearly hands‑free: once the outline and voice rules are in place, a single command triggers every agent in sequence. The automation reuses prior research and embeddings so chapters evolve coherently without re‑inventing earlier sections. You remain in control through editable text files and version control while the heavy lifting happens in the cloud.

Documentation files such as `resources.md` (combining the bibliography, figures list, and research log) help track sources and artwork. Short closing stories now appear in `config/outline.yaml`, and `docs/closing-stories.md` explains their purpose.

## Installation

Clone the repository and install dependencies before running the pipeline:

```bash
git clone <repository-url>
cd FFK-Book
pip install -r requirements.txt
```

## Basic Usage

1. Edit `config/outline.yaml` to list chapters, mark each with `parts: 2`, and specify a short closing story.
2. Adjust `config/style.md` or `docs/style-guide.md` for tone rules.
3. Provide your OpenAI API key in `config/openai.toml` or set `OPENAI_API_KEY` in your environment.
   If no key is found, the pipeline will prompt you for it when you start.
4. Run `python run_pipeline.py` to launch the agent cycle and generate drafts in `drafts/`.
5. Each chapter will produce two files (`section_<id>_part1.md` and `section_<id>_part2.md`).
6. Review drafts and open pull requests with improvements.

## Quick Start

Once dependencies are installed and your API key is configured (via environment variable or `config/openai.toml`), run the basic
pipeline with:

```bash
python run_pipeline.py
```

New drafts appear under `drafts/`. Before submitting any pull request, run the
test suite to verify structure:

```bash
pytest -q
```

These tests ensure every chapter includes a closing story and that required
directories exist.

## Agent Workflow

The pipeline coordinates several GPT‑4.1 agents with distinct roles. A
`ResearchAgent` gathers facts and citations, feeding a `PromptBuilder`
that crafts the exact instruction set for the `DraftWriter`. Drafts are
checked by a `ReviewerAgent`, optionally rewritten once, and then
committed via an `UpdaterAgent` that updates cached embeddings. Token
budgets keep each call under half the model limits to avoid truncation.

## Closing Stories

Each chapter concludes with a short Kabbalistic or historical story. These vignettes are humorous yet accurate, inviting contemplation rather than giving simple answers. A brief description for each story is stored in `config/outline.yaml`, and `docs/closing-stories.md` summarizes the overall approach.

## Project Structure

- `config/` contains the outline, style guide, and OpenAI settings.
- `drafts/` and `reviews/` hold generated sections and review diffs.
- `data/` caches research JSON and text embeddings.
- `assets/` stores an image plan for later illustration work.

## Contribution Guidelines

Contributions are welcome! Keep pull requests focused and document the rationale behind your changes. Please run `pytest -q` before committing so automated checks pass. Feel free to open issues with questions or suggestions.
