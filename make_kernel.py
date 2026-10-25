import json
import os
from pathlib import Path

kernel_dir = Path("d:/AI Research/gemma_paper/kaggle_kernel")
kernel_dir.mkdir(parents=True, exist_ok=True)

def read(p):
    with open(p, "r", encoding="utf-8") as f:
        return f.read()

agent_yaml = read("d:/AI Research/gemma_paper/agent_sfd/agent.yaml")
eval_cfg = read("d:/AI Research/gemma_paper/agent_sfd/eval_config.yaml")
sampling_yaml = read("d:/AI Research/gemma_paper/agent_sfd/configs/sampling.yaml")
triage_agent_yaml = read("d:/AI Research/gemma_paper/agent_sfd/sub_agents/triage_agent.yaml")
patch_agent_yaml = read("d:/AI Research/gemma_paper/agent_sfd/sub_agents/patch_agent.yaml")
verifier_agent_yaml = read("d:/AI Research/gemma_paper/agent_sfd/sub_agents/verifier_agent.yaml")
triage_prompt = read("d:/AI Research/gemma_paper/agent_sfd/prompts/triage.md")
patcher_prompt = read("d:/AI Research/gemma_paper/agent_sfd/prompts/patcher.md")
verifier_prompt = read("d:/AI Research/gemma_paper/agent_sfd/prompts/verifier.md")

code_cell_2 = f'''agent_yaml_content = {repr(agent_yaml)}
eval_cfg_content = {repr(eval_cfg)}
sampling_yaml_content = {repr(sampling_yaml)}
triage_agent_content = {repr(triage_agent_yaml)}
patch_agent_content = {repr(patch_agent_yaml)}
verifier_agent_content = {repr(verifier_agent_yaml)}
triage_prompt_content = {repr(triage_prompt)}
patcher_prompt_content = {repr(patcher_prompt)}
verifier_prompt_content = {repr(verifier_prompt)}

# Write files to AGENT_DIR
(AGENT_DIR / "agent.yaml").write_text(agent_yaml_content, encoding="utf-8")
(AGENT_DIR / "eval_config.yaml").write_text(eval_cfg_content, encoding="utf-8")
(AGENT_DIR / "configs" / "sampling.yaml").write_text(sampling_yaml_content, encoding="utf-8")
(AGENT_DIR / "sub_agents" / "triage_agent.yaml").write_text(triage_agent_content, encoding="utf-8")
(AGENT_DIR / "sub_agents" / "patch_agent.yaml").write_text(patch_agent_content, encoding="utf-8")
(AGENT_DIR / "sub_agents" / "verifier_agent.yaml").write_text(verifier_agent_content, encoding="utf-8")
(AGENT_DIR / "prompts" / "triage.md").write_text(triage_prompt_content, encoding="utf-8")
(AGENT_DIR / "prompts" / "patcher.md").write_text(patcher_prompt_content, encoding="utf-8")
(AGENT_DIR / "prompts" / "verifier.md").write_text(verifier_prompt_content, encoding="utf-8")

print("Declarative agent tree written successfully.")
'''

code_cell_3 = '''# Package into /kaggle/working/submission.zip with agent.yaml at root
zip_base = WORKING_DIR / "submission"
zip_path = Path(shutil.make_archive(str(zip_base), "zip", root_dir=AGENT_DIR))

# Validate archive contents
with zipfile.ZipFile(zip_path, "r") as zf:
    names = zf.namelist()
    assert "agent.yaml" in names, "Missing agent.yaml at root of submission.zip!"
    print(f"Created {zip_path.name} ({zip_path.stat().st_size} bytes)")
    print("Archive entries:")
    for n in sorted(names):
        print(f"  - {n}")
'''

cells = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# State-Filtered Deliberation (SFD) Developer Agent\n",
            "### Official Submission for The Gemma 4 Developer Agent Competition\n",
            "**Author:** Karandeep Singh Sodhi (karandeep.sodhi2504a@gmail.com)\n",
            "**Paper Writeup:** *State-Filtered Deliberation: Eliminating Trajectory Entropy for Small Gemma-4 Developer Agents*\n",
            "\n",
            "This notebook packages the complete, zero-dependency declarative `submission.zip` archive implementing **State-Filtered Deliberation (SFD)** with **Markovian Context Folding (MCF)**.\n"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import os\n",
            "import shutil\n",
            "import zipfile\n",
            "from pathlib import Path\n",
            "\n",
            "WORKING_DIR = Path(\"/kaggle/working\")\n",
            "AGENT_DIR = WORKING_DIR / \"agent_sfd\"\n",
            "AGENT_DIR.mkdir(parents=True, exist_ok=True)\n",
            "(AGENT_DIR / \"configs\").mkdir(exist_ok=True)\n",
            "(AGENT_DIR / \"prompts\").mkdir(exist_ok=True)\n",
            "(AGENT_DIR / \"sub_agents\").mkdir(exist_ok=True)\n",
            "\n",
            "print(\"Building SFD agent structure...\")\n"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [code_cell_2]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [code_cell_3]
    }
]

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.10.0"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 5
}

with open(kernel_dir / "sfd_developer_agent.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2)

metadata = {
    "id": "karandeepsinghsodhi/sfd-gemma-4-developer-agent",
    "title": "SFD: State-Filtered Deliberation Agent (Gemma-4)",
    "code_file": "sfd_developer_agent.ipynb",
    "language": "python",
    "kernel_type": "notebook",
    "is_private": False,
    "enable_gpu": False,
    "enable_internet": False,
    "dataset_sources": [],
    "competition_sources": ["gemma-4-developer-agent"],
    "kernel_sources": []
}

with open(kernel_dir / "kernel-metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2)

print("Kaggle kernel files created successfully in:", kernel_dir)
