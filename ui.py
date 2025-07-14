import os
import threading
import io
import contextlib
from pathlib import Path

import toml
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog

import run_pipeline


class PipelineUI:
    def __init__(self, master: tk.Tk):
        self.master = master
        master.title("FFK Book Pipeline")
        row = 0
        tk.Label(master, text="OpenAI API Key:").grid(row=row, column=0, sticky="e")
        self.api_key = tk.Entry(master, show="*", width=50)
        self.api_key.grid(row=row, column=1, sticky="w")
        row += 1
        tk.Label(master, text="Organization:").grid(row=row, column=0, sticky="e")
        self.org = tk.Entry(master, width=50)
        self.org.grid(row=row, column=1, sticky="w")
        row += 1

        self.model_vars = {}
        for name in ["code_pro", "long_1M", "review_64k", "fast_8k"]:
            tk.Label(master, text=f"Model {name}:").grid(row=row, column=0, sticky="e")
            entry = tk.Entry(master, width=30)
            entry.grid(row=row, column=1, sticky="w")
            self.model_vars[name] = entry
            row += 1

        tk.Button(master, text="Run Pipeline", command=self.run_pipeline).grid(row=row, column=0)
        tk.Button(master, text="Save Settings", command=self.save_settings).grid(row=row, column=1)
        row += 1
        self.log = scrolledtext.ScrolledText(master, width=80, height=20)
        self.log.grid(row=row, column=0, columnspan=2)

        self.load_settings()

    def ask_user(self, prompt: str) -> str:
        if messagebox.askyesno("Pipeline Question", prompt):
            return "y"
        return "n"

    def load_settings(self):
        cfg_path = Path("config/openai.toml")
        if cfg_path.exists():
            data = toml.loads(cfg_path.read_text())
            self.api_key.insert(0, data.get("openai", {}).get("api_key", ""))
            self.org.insert(0, data.get("openai", {}).get("organization", ""))
            models = data.get("models", {})
            for k, entry in self.model_vars.items():
                entry.insert(0, models.get(k, ""))

    def save_settings(self):
        data = {
            "openai": {
                "api_key": self.api_key.get().strip(),
                "organization": self.org.get().strip(),
            },
            "models": {k: e.get().strip() for k, e in self.model_vars.items()},
        }
        Path("config").mkdir(exist_ok=True)
        Path("config/openai.toml").write_text(toml.dumps(data))
        self.log.insert(tk.END, "Settings saved\n")

    def run_pipeline(self):
        self.save_settings()
        os.environ["OPENAI_API_KEY"] = self.api_key.get().strip()
        self.log.delete("1.0", tk.END)

        def target():
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                run_pipeline.main(prompt_fn=self.ask_user)
            output = buf.getvalue()
            self.log.insert(tk.END, output)

        threading.Thread(target=target, daemon=True).start()


def main():
    root = tk.Tk()
    PipelineUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
