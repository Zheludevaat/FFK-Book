"""Simplified agent workflow skeleton implementing the main roles."""

import toml
import yaml
import openai
import os
import json
from pathlib import Path

CONFIG_DIR = Path('config')
DRAFTS_DIR = Path('drafts')
SUMMARY_DIR = DRAFTS_DIR / 'summaries'


def load_outline():
    outline_path = CONFIG_DIR / 'outline.yaml'
    return yaml.safe_load(outline_path.read_text())


def load_style():
    return (CONFIG_DIR / 'style.md').read_text()


def load_openai_config():
    conf = toml.loads((CONFIG_DIR / 'openai.toml').read_text())
    return {
        'api_key': conf.get('openai', {}).get('api_key'),
        'organization': conf.get('openai', {}).get('organization'),
        'models': conf.get('models', {}),
    }


class ResearchAgent:
    def __init__(self, client, model: str):
        self.client = client
        self.model = model

    def run(self, chapter, part: int):
        print(f"[Research] Gathering facts for chapter {chapter['id']} part {part}")
        messages = [
            {"role": "system", "content": "You are a research assistant."},
            {
                "role": "user",
                "content": f"List key facts with citations for {chapter['title']}.",
            },
        ]
        try:
            resp = self.client.chat.completions.create(
                model=self.model, messages=messages, max_tokens=2048
            )
            content = resp.choices[0].message.content
        except Exception as e:
            print(f"Research error: {e}")
            content = ""
        image_entry = {
            "id": f"ch{chapter['id']:03d}_p{part}",
            "placement": f"chapter-{chapter['id']}-part{part}",
            "caption": f"Placeholder image for {chapter['title']} part {part}"
        }
        result = {"facts": content, "images": [image_entry]}
        cache_dir = Path('data/research_cache')
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"chapter_{chapter['id']:03d}_part{part}.json"
        cache_file.write_text(json.dumps(result, indent=2))

        plan_path = Path('assets/_images_plan.yaml')
        if plan_path.exists():
            plan = yaml.safe_load(plan_path.read_text())
        else:
            plan = {"images": []}
        plan.setdefault("images", []).append(image_entry)
        plan_path.write_text(yaml.safe_dump(plan, sort_keys=False))

        return result


class PromptBuilder:
    def __init__(self, client, model: str):
        self.client = client
        self.model = model

    def run(self, research, style, chapter, part: int, final_part: bool, summaries: str = ""):
        messages = [
            {"role": "system", "content": "You craft writing prompts."},
            {
                "role": "user",
                "content": (
                    f"Using the following style guide:\n{style}\n"
                    f"and these research notes:\n{research['facts']}\n"
                    f"Create concise instructions for drafting part {part} of chapter '{chapter['title']}'.\n"
                    + (f"Closing story: {chapter.get('closing_story','')}" if final_part else "")
                    + (f"\nContext summaries:\n{summaries}" if summaries else "")
                ),
            },
        ]
        import tiktoken
        try:
            enc = tiktoken.encoding_for_model(self.model)
        except Exception:
            enc = tiktoken.get_encoding("cl100k_base")
        tokens = sum(len(enc.encode(m["content"])) for m in messages)
        if tokens > 400:
            over = tokens - 400
            facts_tokens = enc.encode(research["facts"])
            if over < len(facts_tokens):
                trimmed = enc.decode(facts_tokens[:-over])
            else:
                trimmed = ""
            messages[1]["content"] = messages[1]["content"].replace(research["facts"], trimmed)
            tokens = sum(len(enc.encode(m["content"])) for m in messages)
            if tokens > 400:
                print(f"[PromptBuilder] warning: prompt still {tokens} tokens")
        resp = self.client.chat.completions.create(
            model=self.model, messages=messages, max_tokens=400
        )
        return resp.choices[0].message.content


class DraftWriter:
    def __init__(self, client, model: str):
        self.client = client
        self.model = model

    def run(self, prompt, chapter_id, part: int):
        print(f"[DraftWriter] Writing draft for chapter {chapter_id} part {part}")
        path = DRAFTS_DIR / f"section_{chapter_id:03d}_part{part}.md"
        messages = [{"role": "system", "content": prompt}]
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=4000,
            )
            content = resp.choices[0].message.content
        except Exception as e:
            print(f"Draft error: {e}")
            content = "# Draft placeholder\n"
        path.write_text(content)
        return path


class SummarizerAgent:
    def __init__(self, client, model: str):
        self.client = client
        self.model = model

    def run(self, draft_path):
        print(f"[Summarizer] Summarizing {draft_path}")
        text = draft_path.read_text()
        messages = [
            {"role": "system", "content": "You create concise summaries."},
            {"role": "user", "content": f"Summarize in about 400 words:\n{text}"},
        ]
        try:
            resp = self.client.chat.completions.create(
                model=self.model, messages=messages, max_tokens=512
            )
            summary = resp.choices[0].message.content
        except Exception as e:
            print(f"Summary error: {e}")
            summary = text[:400]
        SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
        out_path = SUMMARY_DIR / f"{draft_path.stem}.summary.md"
        out_path.write_text(summary)
        return out_path


class RewriterAgent:
    def __init__(self, client, model: str):
        self.client = client
        self.model = model

    def run(self, draft_path, feedback: str):
        print(f"[Rewriter] Revising {draft_path}")
        text = draft_path.read_text()
        messages = [
            {"role": "system", "content": "You rewrite drafts based on review notes."},
            {
                "role": "user",
                "content": f"Draft:\n{text}\n\nFeedback:\n{feedback}\n\nRewrite with corrections applied.",
            },
        ]
        try:
            resp = self.client.chat.completions.create(
                model=self.model, messages=messages, max_tokens=4096
            )
            new_text = resp.choices[0].message.content
            draft_path.write_text(new_text)
        except Exception as e:
            print(f"Rewrite error: {e}")
        return draft_path


class ReviewerAgent:
    def __init__(self, client, model: str):
        self.client = client
        self.model = model

    def run(self, draft_path):
        print(f"[Reviewer] Checking {draft_path}")
        content = draft_path.read_text()
        messages = [
            {"role": "system", "content": "You review drafts for style and facts."},
            {"role": "user", "content": content},
        ]
        verdict = ""
        try:
            resp = self.client.chat.completions.create(
                model=self.model, messages=messages, max_tokens=1600
            )
            verdict = resp.choices[0].message.content
        except Exception as e:
            verdict = f"ERROR: {e}"
            print(f"Review error: {e}")
        print(verdict)
        text = verdict.lower()
        approved = any(k in text for k in ["accept", "approve", "pass"])
        return approved, verdict

    def chapter_checkpoint(self, chapter_id, parts, prompt_user=input):
        print(f"[Reviewer] Chapter {chapter_id} checkpoint")
        texts = []
        for p in parts:
            path = DRAFTS_DIR / f"section_{chapter_id:03d}_part{p}.md"
            if path.exists():
                texts.append(path.read_text())
        if not texts:
            return False
        content = "\n\n".join(texts)
        messages = [
            {"role": "system", "content": "Check the chapter for drift or contradictions."},
            {"role": "user", "content": content},
        ]
        verdict = ""
        try:
            resp = self.client.chat.completions.create(
                model=self.model, messages=messages, max_tokens=1600
            )
            verdict = resp.choices[0].message.content
            print(verdict)
        except Exception as e:
            verdict = f"ERROR: {e}"
            print(f"Chapter review error: {e}")
        if "error" in verdict.lower() or "fail" in verdict.lower() or "reject" in verdict.lower():
            ans = prompt_user("Checkpoint issues detected. Continue? [y/N] ")
            return ans.strip().lower().startswith("y")
        return True


class UpdaterAgent:
    def __init__(self, client, model: str = "text-embedding-3-small"):
        self.client = client
        self.model = model

    def run(self, draft_path):
        print(f"[Updater] Embedding {draft_path}")
        try:
            resp = self.client.embeddings.create(input=draft_path.read_text(), model=self.model)
            vec = resp.data[0].embedding
            out_dir = Path('data/chroma')
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / f"{draft_path.stem}.json"
            out_file.write_text(json.dumps({'embedding': vec}, indent=2))
            return out_file
        except Exception as e:
            print(f"Embedding error: {e}")
            return None


def main(prompt_fn=input):
    outline = load_outline()
    style = load_style()
    cfg = load_openai_config()
    env_key = os.getenv('OPENAI_API_KEY')
    api_key = env_key or cfg['api_key']
    if not api_key or api_key == 'sk-your-key':
        api_key = prompt_fn('Enter your OpenAI API key: ').strip()
    org = cfg.get('organization') or None
    client = openai.OpenAI(api_key=api_key, organization=org)
    chapters = outline.get('chapters', [])
    print('Loaded outline with', len(chapters), 'chapters')

    DRAFTS_DIR.mkdir(exist_ok=True)
    models = cfg.get('models', {})
    research = ResearchAgent(client, models.get('fast_8k', 'gpt-4.1'))
    prompter = PromptBuilder(client, models.get('code_pro', 'gpt-4.1'))
    writer = DraftWriter(client, models.get('long_1M', 'gpt-4.1'))
    reviewer = ReviewerAgent(client, models.get('review_64k', 'gpt-4.1'))
    rewriter = RewriterAgent(client, models.get('long_1M', 'gpt-4.1'))
    updater = UpdaterAgent(client)
    summarizer = SummarizerAgent(client, models.get('fast_8k', 'gpt-4.1'))
    SUMMARY_DIR.mkdir(exist_ok=True)
    chapter_summaries = {}

    for ch in chapters:
        parts = ch.get('parts', 1)
        this_summaries = []
        for part in range(1, parts + 1):
            prior = "\n\n".join(chapter_summaries.get(cid, "") for cid in sorted(chapter_summaries))
            if this_summaries:
                prior = (prior + "\n\n" if prior else "") + "\n\n".join(this_summaries)
            print(f"\nProcessing Chapter {ch['id']} Part {part}: {ch['title']}")
            res = research.run(ch, part)
            final_part = part == parts
            prompt = prompter.run(res, style, ch, part, final_part, prior)
            draft_path = writer.run(prompt, ch['id'], part)
            approved, notes = reviewer.run(draft_path)
            if not approved:
                print("Reviewer suggestions:\n", notes)
                ans = prompt_fn("Apply automatic rewrite? [y/N] ")
                if ans.strip().lower().startswith('y'):
                    rewriter.run(draft_path, notes)
                    approved, notes = reviewer.run(draft_path)
                    print(notes)
            if approved or prompt_fn("Draft still has issues. Continue anyway? [y/N] ").lower().startswith('y'):
                emb_path = updater.run(draft_path)
                if emb_path:
                    print(f"[Updater] Wrote {emb_path}")
                sum_path = summarizer.run(draft_path)
                this_summaries.append(sum_path.read_text())
        chapter_summaries[ch['id']] = "\n\n".join(this_summaries)
        if parts > 1:
            reviewer.chapter_checkpoint(ch['id'], list(range(1, parts + 1)), prompt_fn)



if __name__ == '__main__':
    main()
