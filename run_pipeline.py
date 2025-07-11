"""Simplified agent workflow skeleton implementing the main roles."""

import toml
import yaml
import openai
import os
import json
from pathlib import Path

CONFIG_DIR = Path('config')
DRAFTS_DIR = Path('drafts')


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

    def run(self, research, style, chapter, part: int, final_part: bool):
        print(f"[PromptBuilder] Creating prompt for chapter {chapter['id']} part {part}")
        messages = [
            {"role": "system", "content": "You craft writing prompts."},
            {
                "role": "user",
                "content": (
                    f"Using the following style guide:\n{style}\n"
                    f"and these research notes:\n{research['facts']}\n"
                    f"Create concise instructions for drafting part {part} of chapter '{chapter['title']}'.\n"
                    + (f"Closing story: {chapter.get('closing_story','')}" if final_part else "")
                ),
            },
        ]
        try:
            resp = self.client.chat.completions.create(
                model=self.model, messages=messages, max_tokens=400
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f"Prompt error: {e}")
            return "Draft the chapter using provided facts"


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
        try:
            resp = self.client.chat.completions.create(
                model=self.model, messages=messages, max_tokens=1600
            )
            verdict = resp.choices[0].message.content
            print(verdict)
        except Exception as e:
            print(f"Review error: {e}")
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
        except Exception as e:
            print(f"Embedding error: {e}")


def main():
    outline = load_outline()
    style = load_style()
    cfg = load_openai_config()
    env_key = os.getenv('OPENAI_API_KEY')
    api_key = env_key or cfg['api_key']
    if not api_key or api_key == 'sk-your-key':
        api_key = input('Enter your OpenAI API key: ').strip()
    org = cfg.get('organization') or None
    client = openai.OpenAI(api_key=api_key, organization=org)
    chapters = outline.get('chapters', [])
    print('Loaded outline with', len(chapters), 'chapters')

    DRAFTS_DIR.mkdir(exist_ok=True)
    models = cfg.get('models', {})
    research = ResearchAgent(client, models.get('fast_8k', 'gpt-4.1-fast-8k'))
    prompter = PromptBuilder(client, models.get('code_pro', 'gpt-4.1-code-pro-2025-07'))
    writer = DraftWriter(client, models.get('long_1M', 'gpt-4.1-long-1M'))
    reviewer = ReviewerAgent(client, models.get('review_64k', 'gpt-4.1-review-64k'))
    updater = UpdaterAgent(client)

    for ch in chapters:
        parts = ch.get('parts', 1)
        for part in range(1, parts + 1):
            print(f"\nProcessing Chapter {ch['id']} Part {part}: {ch['title']}")
            res = research.run(ch, part)
            final_part = part == parts
            prompt = prompter.run(res, style, ch, part, final_part)
            draft_path = writer.run(prompt, ch['id'], part)
            if reviewer.run(draft_path):
                updater.run(draft_path)



if __name__ == '__main__':
    main()
