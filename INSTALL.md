# Terraform from Diagram — Skill Package

Drop the `.claude/` folder into any project root to activate all commands.

---

## Installation

```bash
# Copy the .claude folder into your project root
cp -r .claude/ /path/to/your-project/

# Your project structure after install:
your-project/
├── .claude/
│   ├── commands/          ← slash commands registered in Claude Code
│   │   ├── Diagram2Services.md
│   │   ├── ServicesRefiner.md
│   │   ├── ServiceModeler.md
│   │   ├── BuildPlan.md
│   │   ├── ServiceBuilder.md
│   │   ├── tf-cost.md
│   │   ├── DeployOrchestrator.md
│   │   ├── tf-status.md
│   │   ├── tf-resume.md
│   │   ├── tf-reset.md
│   │   ├── help.md
│   │   └── ...
│   ├── skills/
│   │   └── terraform-from-diagram/
│   │       ├── SKILL.md          ← main skill instructions
│   │       ├── references/       ← detailed guides loaded per command
│   │       ├── templates/        ← terraform module templates
│   │       └── review/           ← gate review files written here
│   └── memory/                   ← auto-created when skill runs
└── (your project files)
```

## Then open in VS Code

```bash
code your-project/
```

Or open via a `.code-workspace` file if you have one.

## Commands available after install

```
/Diagram2Services    parse your .drawio diagram
/ServicesRefiner     review service names
/ServiceModeler      review build order
/BuildPlan           collect config per wave
/ServiceBuilder      build next service
/ServiceBuilder wave:N  build entire wave N
/tf-cost             estimate monthly AWS costs
/DeployOrchestrator  generate CI/CD files
/tf-status           wave-by-wave project status
/help                full guide + next step
/tf-resume           continue after a break
/tf-reset            start over
```

## Requirements

- VS Code with Claude Code extension installed
- Signed in to claude.ai
- `brew install terraform awscli tflint checkov infracost`
