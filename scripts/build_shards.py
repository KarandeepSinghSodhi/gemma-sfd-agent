import ast
import json
import shutil
from pathlib import Path

# Load base build_eval_notebook logic
DOCKER_IMAGE = "gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461"
MACHINE_SHAPE = "NvidiaL4"

# Read cell definitions from kaggle_kernel_shard2/sfd_eval_shard2.ipynb
shard2_nb_path = Path(r"d:\AI Research\gemma_paper\kaggle_kernel_shard2\sfd_eval_shard2.ipynb")
assert shard2_nb_path.exists(), "Shard 2 notebook not found"
base_nb = json.loads(shard2_nb_path.read_text(encoding="utf-8"))

# Shard 3 Tasks (seed 43, disjoint from Cohort 1 & Cohort 2):
# Cohort 1: fastapi_15661, fastapi_15588, fastapi_15589, requests_7505, requests_7502, rich_4070, rich_4077, httpx_3672
# Cohort 2: rich_3043, rich_3944, rich_4076, fastapi_14361, fastapi_9753, fastapi_14459, fastapi_14099, requests_7427
# Shard 3: fastapi_15280, fastapi_14372, fastapi_14077, fastapi_14371, rich_3894, rich_3471, rich_3535, requests_7315
# Shard 4: fastapi_14455, fastapi_5624, fastapi_14419, fastapi_15785, rich_3938, rich_3930, rich_3480, requests_7205

def create_shard_notebook(shard_num: int, task_ids: list[str], output_dir: Path, kernel_id: str, title: str):
    output_dir.mkdir(parents=True, exist_ok=True)
    nb = json.loads(json.dumps(base_nb))
    
    # In Cell 4 (execution cell), replace task selection with explicit list of task IDs
    c4_lines = nb["cells"][3]["source"]
    c4_text = "".join(c4_lines)
    
    # We want to replace the task selection block in cell 4
    # Find start of selection and end before CONFIGS =
    split_start = "TASKS_PATH = DATA_DIR / 'tasks.jsonl'"
    split_end = "CONFIGS = {"
    assert split_start in c4_text, "split_start not found in cell 4"
    assert split_end in c4_text, "split_end not found in cell 4"
    
    prefix = c4_text[:c4_text.find(split_start) + len(split_start)]
    suffix = c4_text[c4_text.find(split_end):]
    
    task_ids_str = json.dumps(task_ids)
    
    custom_selection = f"""
all_tasks = load_tasks(TASKS_PATH)
TARGET_IDS = {task_ids_str}
BENCHMARK_TASKS = [t for t in all_tasks if t.instance_id in TARGET_IDS]
# Preserve order of TARGET_IDS
id_to_task = {{t.instance_id: t for t in BENCHMARK_TASKS}}
BENCHMARK_TASKS = [id_to_task[tid] for tid in TARGET_IDS if tid in id_to_task]

print(f'Selected {{len(BENCHMARK_TASKS)}} benchmark tasks for Shard {shard_num}:')
for idx, t in enumerate(BENCHMARK_TASKS, 1):
    print(f'  [{{idx}}] {{t.instance_id}} ({{t.repo}})')

"""
    new_c4_text = prefix + "\n" + custom_selection + "\n" + suffix
    ast.parse(new_c4_text)  # Verify python syntax
    
    nb["cells"][3]["source"] = new_c4_text.splitlines(keepends=True)
    
    code_file = f"sfd_eval_shard{shard_num}.ipynb"
    (output_dir / code_file).write_text(json.dumps(nb, indent=2), encoding="utf-8")
    
    meta = {
        "id": kernel_id,
        "title": title,
        "code_file": code_file,
        "language": "python",
        "kernel_type": "notebook",
        "is_private": False,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": False,
        "keywords": ["gpu"],
        "dataset_sources": ["metric/gemma-4-developer-agent-wheelhouse"],
        "kernel_sources": [],
        "competition_sources": ["gemma-4-developer-agent"],
        "model_sources": [
            "google/gemma-4/Other/gemma-4-e4b-it-qat-w4a16-ct/2",
            "google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2",
            "google/gemma-4/Other/gemma-4-e2b-it-qat-w4a16-ct/2",
            "google/gemma-4/Other/gemma-4-12b-it-qat-w4a16-ct/2",
        ],
        "docker_image": DOCKER_IMAGE,
        "machine_shape": MACHINE_SHAPE,
    }
    (output_dir / "kernel-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Generated Shard {shard_num} in {output_dir}")

# Shard 3: 8 tasks
s3_tasks = ['fastapi_15280', 'fastapi_14372', 'fastapi_14077', 'fastapi_14371', 'rich_3894', 'rich_3471', 'rich_3535', 'requests_7315']
create_shard_notebook(
    shard_num=3,
    task_ids=s3_tasks,
    output_dir=Path(r"d:\AI Research\gemma_paper\kaggle_kernel_shard3"),
    kernel_id="karandeepsinghsodhi/sfd-paired-eval-shard-3-gemma-4",
    title="SFD Paired Eval Shard 3 Gemma 4"
)

# Shard 4: 8 tasks
s4_tasks = ['fastapi_14455', 'fastapi_5624', 'fastapi_14419', 'fastapi_15785', 'rich_3938', 'rich_3930', 'rich_3480', 'requests_7205']
create_shard_notebook(
    shard_num=4,
    task_ids=s4_tasks,
    output_dir=Path(r"d:\AI Research\gemma_paper\kaggle_kernel_shard4"),
    kernel_id="karandeepsinghsodhi/sfd-paired-eval-shard-4-gemma-4",
    title="SFD Paired Eval Shard 4 Gemma 4"
)
