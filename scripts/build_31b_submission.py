import os
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src_dir = ROOT / "agent_sfd"
out_dir = ROOT / "agent_sfd_31b_v2"
out_dir.mkdir(parents=True, exist_ok=True)

# Copy base tree
for sub in ["configs", "prompts", "sub_agents"]:
    dest = out_dir / sub
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src_dir / sub, dest)

shutil.copy2(src_dir / "agent.yaml", out_dir / "agent.yaml")

# Write optimized eval_config.yaml (guaranteed safe runtime: max 2.0 min/task)
eval_cfg = """# Optimized evaluation configuration for 31B SFD Agent
# Strictly guarantees completion inside the Kaggle 12-hour evaluation window
evaluation:
  timeout_seconds: 75
  verification_timeout_seconds: 60
  max_tool_calls: 12
  max_time_minutes: 2.0
  max_turns: 25
"""
(out_dir / "eval_config.yaml").write_text(eval_cfg, encoding="utf-8")

# Write deterministic sampling.yaml
sampling_cfg = """temperature: 0.0
top_p: 0.95
max_output_tokens: 8192
thinking_config:
  thinking_budget: 1536
  include_thoughts: true
"""
(out_dir / "configs" / "sampling.yaml").write_text(sampling_cfg, encoding="utf-8")

# Ensure sub_agents all use gemma-4-31b-it-qat-w4a16-ct
for sa in ["triage_agent.yaml", "patch_agent.yaml", "verifier_agent.yaml"]:
    sa_path = out_dir / "sub_agents" / sa
    content = sa_path.read_text(encoding="utf-8")
    assert "gemma-4-31b-it-qat-w4a16-ct" in content, f"Missing 31B in {sa}"

# Enhance verifier prompt with syntax check instruction
verifier_path = out_dir / "prompts" / "verifier.md"
verifier_prompt = verifier_path.read_text(encoding="utf-8")
if "py_compile" not in verifier_prompt:
    enhanced = verifier_prompt.replace(
        "1. Call `run_command` with `git status`",
        "1. Call `run_command` with `git status` to verify modified files.\n   - Run `python -m py_compile <modified_file>` to confirm zero SyntaxErrors before testing."
    )
    verifier_path.write_text(enhanced, encoding="utf-8")

# Package into submission ZIP
zip_path = ROOT / "submission_sfd_31b_v2.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(out_dir):
        for f in files:
            full_path = Path(root) / f
            arcname = full_path.relative_to(out_dir).as_posix()
            z.write(full_path, arcname)

print("Packaged submission_sfd_31b_v2.zip successfully!")
with zipfile.ZipFile(zip_path, "r") as z:
    print("Zip contents:")
    for info in z.infolist():
        print(f"  {info.filename} ({info.file_size} bytes)")
