#!/bin/bash

# JIRA Ticket Fetcher Helper Script
# Fetches JIRA work item details using the Atlassian CLI (acli)
#
# Usage: ./fetch_jira_ticket.sh KEY-123 [--fields field1,field2] [--json] [--web]
#
# Examples:
#   ./fetch_jira_ticket.sh KEY-123
#   ./fetch_jira_ticket.sh KEY-123 --fields summary,status,assignee
#   ./fetch_jira_ticket.sh KEY-123 --json
#   ./fetch_jira_ticket.sh KEY-123 --web

set -e

# Check if a work item key was provided
if [ $# -lt 1 ]; then
    echo "Error: Work item key required"
    echo ""
    echo "Usage: $0 KEY-123 [--fields field1,field2] [--json] [--web]"
    echo ""
    echo "Examples:"
    echo "  $0 KEY-123"
    echo "  $0 KEY-123 --fields summary,status,assignee"
    echo "  $0 KEY-123 --json"
    echo "  $0 KEY-123 --web"
    exit 1
fi

# Check if acli is installed
if ! command -v acli &> /dev/null; then
    echo "Error: acli is not installed or not found in PATH"
    echo "Please install acli following the guide:"
    echo "https://developer.atlassian.com/cloud/acli/guides/install-acli/"
    exit 1
fi

WORK_ITEM_KEY="$1"
shift  # Remove first argument

# Pass remaining arguments to acli
acli jira workitem view "$WORK_ITEM_KEY" "$@"
