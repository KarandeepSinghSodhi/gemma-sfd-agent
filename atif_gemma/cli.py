"""
Command-Line Interface for the ATIF-Gemma Diagnostic Suite.
"""
import argparse
import json
import sys
from pathlib import Path
from .audit import audit_corpus, parse_trace_file
from .taxonomy import classify_trace_exit_code, classify_failure_bucket
from .remediation import get_remediation_playbook

def main():
    parser = argparse.ArgumentParser(description="ATIF-Gemma: Diagnostic Toolkit for SWE Agents")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")
    
    # Audit command
    audit_parser = subparsers.add_parser("audit", help="Audit a folder of ATIF v1.7 traces")
    audit_parser.add_argument("dir", type=str, help="Path to directory containing trace_*.json files")
    
    # Inspect command
    inspect_parser = subparsers.add_parser("inspect", help="Inspect a single ATIF trace file")
    inspect_parser.add_argument("file", type=str, help="Path to ATIF trace JSON file")
    
    # Playbook command
    subparsers.add_parser("playbook", help="Print the Actionable Remediation Playbook")
    
    args = parser.parse_args()
    
    if args.command == "audit":
        summary = audit_corpus(args.dir)
        print("=" * 60)
        print("  ATIF-GEMMA CORPUS AUDIT REPORT")
        print("=" * 60)
        print(f"Total Traces Analyzed:    {summary['num_traces']}")
        print(f"Total LLM Turns:          {summary['total_llm_turns']}")
        print(f"Total Tool Invocations:   {summary['total_tool_calls']}")
        print(f"Total Tokens Logged:      {summary['total_tokens']:,}")
        print(f"  - Prompt Tokens:        {summary['total_prompt_tokens']:,}")
        print(f"  - Completion Tokens:    {summary['total_completion_tokens']:,}")
        print(f"Syntax/Edit Errors:       {summary['edit_file_errors']}")
        print(f"Budget Exhaustions:       {summary['budget_errors']}")
        print("\nTool Usage Breakdown:")
        for t, c in sorted(summary["tool_distribution"].items(), key=lambda x: -x[1]):
            print(f"  {t:25s}: {c:4d}")
        print("=" * 60)
        
    elif args.command == "inspect":
        info = parse_trace_file(args.file)
        print(json.dumps(info, indent=2))
        
    elif args.command == "playbook":
        pb = get_remediation_playbook()
        print("=" * 70)
        print("  ACTIONABLE REMEDIATION PLAYBOOK FOR SWE AGENTS")
        print("=" * 70)
        for cat, data in pb.items():
            print(f"\n[{cat}]")
            print(f"  Symptom:       {data['symptom']}")
            print(f"  Fix:           {data['architectural_fix']}")
        print("=" * 70)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
