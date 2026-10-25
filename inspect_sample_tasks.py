import json

with open('d:/AI Research/gemma_comp/tasks.jsonl', encoding='utf-8') as f:
    tasks = [json.loads(line) for line in f]

for i in range(5):
    t = tasks[i]
    iid = t['instance_id']
    repo = t['repo']
    prob = t['problem_statement'][:250].replace('\n', ' ').encode('ascii', 'replace').decode('ascii')
    patch = t['patch'][:300].encode('ascii', 'replace').decode('ascii')
    print(f"=== TASK {i}: {iid} ({repo}) ===")
    print(f"Problem: {prob}")
    print(f"Golden Patch snippet:\n{patch}\n")
