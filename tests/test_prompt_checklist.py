import re

CHECKLIST_PATH = 'docs/prompt-checklist.md'

def test_readme_references_checklist():
    with open('README.md') as f:
        text = f.read()
    assert CHECKLIST_PATH in text

def test_style_guide_references_checklist():
    with open('docs/style-guide.md') as f:
        text = f.read()
    assert CHECKLIST_PATH in text
