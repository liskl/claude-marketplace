---
name: jira-ticket-fetcher
description: This skill enables fetching and displaying JIRA ticket details using the Atlassian CLI (acli). This skill should be used when users need to retrieve JIRA work item information, view ticket summaries, comments, or specific fields. It requires acli to be installed and authenticated with an Atlassian account.
---

# JIRA Ticket Fetcher

## Overview

The JIRA Ticket Fetcher skill provides the ability to retrieve detailed information about JIRA work items using the Atlassian CLI (`acli`). This enables quick access to ticket information including summaries, comments, custom fields, and more. The skill handles various viewing options including JSON output and web browser viewing.

## Prerequisites

Before using this skill, ensure:

1. **Install acli**: Follow the [Atlassian CLI installation guide](https://developer.atlassian.com/cloud/acli/guides/install-acli/)
2. **Authenticate**: Run `acli jira auth login --web` to authenticate with your Atlassian account (see [getting started guide](https://developer.atlassian.com/cloud/acli/guides/how-to-get-started/))

## Quick Start

To retrieve a JIRA ticket, use the `fetch_jira_ticket.sh` script with a work item key:

```bash
./scripts/fetch_jira_ticket.sh KEY-123
```

This returns the full ticket details in a readable format.

## Task-Based Operations

### Viewing Ticket Details

To view a work item with its basic information:

```bash
acli jira workitem view KEY-123
```

### Viewing Specific Fields

To view a ticket with only specific fields (e.g., summary and comments):

```bash
acli jira workitem view KEY-123 --fields summary,comment
```

### Exporting as JSON

To retrieve ticket data in JSON format for programmatic processing:

```bash
acli jira workitem view KEY-123 --json
```

### Opening in Web Browser

To open a ticket directly in your web browser:

```bash
acli jira workitem view KEY-123 --web
```

## Common Field Names

When using the `--fields` flag, consider these commonly available fields:

- `summary` - Ticket title/summary
- `description` - Full description
- `status` - Current status
- `assignee` - Person assigned to the ticket
- `reporter` - Person who created the ticket
- `priority` - Priority level
- `labels` - Associated labels
- `comment` - Comments on the ticket
- `created` - Creation timestamp
- `updated` - Last update timestamp

## Helper Script

The `scripts/fetch_jira_ticket.sh` script provides a convenient wrapper that automatically handles common parameters and formats output readably. To use it with additional flags:

```bash
./scripts/fetch_jira_ticket.sh KEY-123 --fields summary,status,assignee
./scripts/fetch_jira_ticket.sh KEY-123 --json
./scripts/fetch_jira_ticket.sh KEY-123 --web
```

## Troubleshooting

### Authentication Issues

If you encounter authentication errors, re-authenticate using:

```bash
acli jira auth login --web
```

### acli Not Found

Ensure acli is installed and added to your PATH. Verify installation with:

```bash
acli --version
```

### Field Not Available

If a specific field is not available for your JIRA instance, omit it and try querying other fields. The `--fields` parameter is optional and JIRA will return basic information if not specified.

## Official References

- [acli Reference - jira workitem view](https://developer.atlassian.com/cloud/acli/reference/commands/jira-workitem-view/)
- [acli Installation Guide](https://developer.atlassian.com/cloud/acli/guides/install-acli/)
- [acli Getting Started](https://developer.atlassian.com/cloud/acli/guides/how-to-get-started/)
