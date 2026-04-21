# claude-marketplace

A Claude Code plugin marketplace with metaskills for collaborative discovery, PRD creation, skill building, and software engineering audits.

## Install

Add the marketplace, then install the plugin you want:

```
/plugin marketplace add liskl/claude-marketplace
/plugin install software-eng-laws@liskl-metaskills
/reload-plugins
```

Swap `software-eng-laws` for any plugin name below.

## Plugins

### `software-eng-laws`
Audit a repository against 56 software engineering laws (Conway, Hyrum, DRY, CAP, etc.). Produces a per-law findings report with evidence citations and a scorecard.

Run after install:
```
/software-eng-laws
```

### `metaskills`
Slash commands for collaborative discovery, PRD creation, and skill building.

- `/metaskills:explore` — light, conversational discovery for new projects or features. Surfaces the questions experienced collaborators ask before jumping to implementation.
- `/metaskills:create-prd` — turns ideas (rough or detailed) into a structured PRD. Adapts depth to input fidelity and outputs Obsidian-optimized or plain markdown.
- `/metaskills:skill-builder` — interview-driven generator that extracts tacit knowledge from a domain expert and emits a Claude Code skill or slash command.

## Layout

```
.claude-plugin/marketplace.json   # marketplace manifest
commands/                         # metaskills plugin (slash commands)
plugins/software-eng-laws/        # software-eng-laws plugin (skill + scripts)
```
