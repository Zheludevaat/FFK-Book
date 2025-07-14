import os

def test_directories_exist():
    for path in [
        'config',
        'data/research_cache',
        'assets',
        'drafts',
        'reviews',
        'data/chroma',
        'drafts/summaries',
    ]:
        assert os.path.isdir(path)


def test_closing_story_present():
    import yaml
    with open('config/outline.yaml') as f:
        data = yaml.safe_load(f)
    for chapter in data.get('chapters', []):
        story = chapter.get('closing_story')
        assert story and isinstance(story, str)

def test_parts_defined():
    import yaml
    with open('config/outline.yaml') as f:
        data = yaml.safe_load(f)
    for chapter in data.get('chapters', []):
        assert chapter.get('parts') == 2
