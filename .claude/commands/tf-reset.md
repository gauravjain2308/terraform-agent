Reset the project memory and start fresh. Generated Terraform files are NOT deleted.

1. Read `.claude/memory/tf-state.json` to get the project name
2. Show a warning and ask for confirmation:
```
⚠️  This will delete all memory for project "{project_name}".
    Your generated Terraform files will NOT be deleted.
    Type "reset" to confirm, or anything else to cancel.
```
3. If user types "reset":
   - Delete all files in `.claude/memory/` except `README.md`
   - Confirm: `✅ Memory cleared. Run /Diagram2Services to begin again.`
4. If user types anything else:
   - Cancel: `Cancelled. Memory unchanged.`
