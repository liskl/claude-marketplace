---
name: route-network-scanner
description: This skill provides comprehensive static analysis of ALL possible network requests for a given URL route. It performs bidirectional analysis (parent providers and child dependencies) and traces all execution contexts including component mounts, user interactions (clicks, form submits), effects, timers/polling, browser events (scroll, resize), state changes, and navigation cleanup. Use this skill when users need a complete, exhaustive list of every network request that COULD occur on a route - including REST API calls, GraphQL queries, third-party SDK calls (Split.io, Contentful, Datadog, etc.), WebSockets, and analytics. The skill dynamically discovers patterns, works with NX monorepos, and provides execution context for each request (when/how it triggers). Output includes all possible requests regardless of conditions, enabling manual verification of completeness.
---

# Route Network Scanner

## Overview

This skill provides comprehensive static analysis of network requests for a given URL route. It dynamically discovers network patterns in the codebase and traces all network calls through the route's dependency tree.

The analysis is performed dynamically using the algorithm described below. No external scripts are required - follow the phases using available tools (Read, Grep, Glob, Bash).

## When to Use This Skill

Use this skill when:
- Analyzing what network requests a specific route makes
- Documenting API dependencies for a route
- Debugging unexpected network calls
- Auditing external requests for security
- Understanding data flow for onboarding
- Planning migrations or refactoring

## Prerequisites

The skill works with:
- NX monorepos (preferred)
- Standard JavaScript/TypeScript repos
- React applications with React Router

## Analysis Workflow

Follow these phases in order. Execute each phase completely before proceeding to the next.

**CRITICAL - Tool Usage**:
- Use ONLY the available tools: Read, Grep, Glob, Bash (for git/npm commands only)
- NEVER attempt to write custom scripts or tools to automate any phase
- All analysis must be performed directly using the available tools
- Breaking this rule will result in incorrect analysis

**IMPORTANT - Timing Tracking**:
- At the START of each phase, note the current time
- At the END of each phase, note the current time and calculate duration
- Store timing metadata for inclusion in final output
- Report phase durations in the Performance Metrics section of the output

**IMPORTANT - Output Location**:
- BEFORE starting Phase 1, ask the user where they want to save the final report
- Suggest default: `./docs/route-analysis/{route-path-sanitized}-{timestamp}.md`
- Get explicit confirmation of the output file path
- Store this path for use in Phase 8

### Phase 1: Repository Bootstrap

**Goal**: Understand the repository structure and locate the target application.

**Steps**:
1. Locate the repository root by checking for:
   - `nx.json` (indicates NX monorepo)
   - `package.json` at root
   - `.git` directory

2. Determine repository type:
   - If `nx.json` exists → NX monorepo
   - If `workspaces` in package.json → Workspace monorepo
   - Otherwise → Standard repo

3. For NX monorepos:
   - Run `nx show projects` to list all apps/libs
   - Identify the target app (ask user if ambiguous)
   - Note the app's root directory (e.g., `apps/consumer-web`)

4. Collect all relevant `package.json` files:
   - Root package.json
   - Target app's package.json (if exists)
   - Workspace package.json files (if applicable)

**Output**: Repository structure understanding and target app directory.

---

### Phase 2: Network Library Discovery

**Goal**: Build a comprehensive manifest of all network-related dependencies in the project.

**Steps**:
1. Read all package.json files collected in Phase 1

2. Extract all dependencies and devDependencies

3. Categorize each dependency:

   **Known HTTP Clients**:
   - axios, superagent, ky, got, request, node-fetch, cross-fetch, isomorphic-fetch

   **Known GraphQL Clients**:
   - @apollo/client, apollo-client, graphql-request, urql, relay-runtime

   **Known Third-Party SDKs**:
   - @splitsoftware/splitio, @splitsoftware/splitio-react
   - contentful, @contentful/rich-text-react-renderer
   - @sentry/browser, @sentry/react, @sentry/node
   - @datadog/browser-rum, @datadog/browser-logs
   - segment, @segment/analytics-next
   - firebase, @firebase/app
   - Any package with "analytics", "tracking", "monitoring" in name

   **WebSocket Libraries**:
   - socket.io-client, ws, websocket

   **Unknown/Heuristic Detection**:
   - Package name contains: "fetch", "request", "http", "api", "client", "sdk"
   - Note these for pattern extraction in Phase 3

4. Build "Dependency Manifest" - a list of all potentially network-related packages with their categories

**Output**: Complete manifest of network-related dependencies to search for.

---

### Phase 3: Import & Usage Pattern Extraction

**Goal**: Discover how each network library is actually used in the codebase.

**Steps**:
1. For each library in the Dependency Manifest:

2. Search for import statements:
   - Use Grep to find: `from ['"]${library}['"]`
   - Also search for: `require(['"]${library}['"])`
   - Capture import syntax variations:
     - `import axios from 'axios'`
     - `import { useQuery } from '@apollo/client'`
     - `import * as Split from '@splitsoftware/splitio'`

3. Analyze usage patterns in files where library is imported:
   - **Function calls**: `axios.get()`, `fetch()`, `client.query()`
   - **React hooks**: `useQuery()`, `useMutation()`, `useLazyQuery()`
   - **Class instantiation**: `new WebSocket()`, `new XMLHttpRequest()`
   - **Method calls**: `splitClient.getTreatment()`, `contentful.getEntry()`

4. Build "Pattern Map" for each library:
   - Library name
   - Common import patterns (what's imported)
   - Common usage patterns (how it's called)
   - Regex patterns to search for in Phase 6

**Output**: Pattern Map containing search patterns for each network library.

---

### Phase 4: Route Resolution

**Goal**: Find the entry component file for the given route path.

**Steps**:
1. Take the route path from user input (e.g., `/login`, `/dashboard/settings`)

2. Determine routing strategy:

   **React Router (Priority Order)**:

   a. **First, check for routesConfig file** (fastest approach):
      - Search for `routesConfig.tsx`, `routesConfig.ts`, `routeConfig.tsx`, or `routeConfig.ts`
      - If found, read the file and look for the route path in the configuration
      - Find the component associated with the path
      - If route found → proceed to Phase 4.5

   b. **If not in routesConfig, search for other route configuration**:
      - Search for route configuration files (grep for `createBrowserRouter`, `<Route`, `<Routes>`)
      - Find the component associated with the path

3. For NX monorepos:
   - Limit search to the target app directory identified in Phase 1
   - Can optionally run `nx show project-graph --file=graph.json` to understand structure

4. If multiple candidates found, present options to user

**Output**: Absolute path to the route's entry component file.

---

### Phase 4.5: Parent Component Discovery (Reverse Traversal)

**Goal**: Discover all parent/wrapper components that wrap the route when it loads.

**Why this matters**: Parent components (providers, layouts, HOCs) often make network requests:
- `SplitProvider` fetches feature flags on mount
- `AuthProvider` checks authentication status
- `ConfigProvider` fetches app configuration
- `AnalyticsProvider` sends pageview events
- Layout components may fetch user profile, notifications, etc.

**Steps**:
1. Initialize reverse traversal:
   - Current file: route component from Phase 4
   - Parent chain: empty list
   - Visited files: empty set (prevent cycles)
   - App root found: false

2. Loop until app root is reached:

   a. **Search for files that import current file**:
      Use Grep to find all import patterns including:
      - Static imports
      - Named imports
      - Lazy loading (`ReactLazyPreload`, `lazy`)
      - Dynamic imports
      - Re-exports

   b. **Handle import results**:
      - If NO files import current file → Reached app root, stop
      - If files found → These are parent components

   c. **For each importing file**:
      - Skip if already visited (prevent cycles)
      - Add to parent chain
      - Mark as visited
      - Add to queue for next iteration

   d. **Detect app root** (stop conditions):
      - No files import current file
      - File is known entry point (`index.tsx`, `main.tsx`, `App.tsx`)

3. Handle multiple import paths and order parent chain

**Output**: Ordered list of parent component files (route → ... → app root)

---

### Phase 5: Dependency Tree Traversal (Bidirectional)

**Goal**: Build a complete list of all application code files that affect the route.

**Steps**:
1. Initialize traversal with route component + all parent components from Phase 4.5
2. For each file, extract all imports (ES6, CommonJS, dynamic)
3. Resolve relative and absolute imports to actual files
4. Add to dependency tree, continue traversal
5. Never traverse into node_modules

**Output**: Complete dependency tree + set of third-party packages imported

---

### Phase 6: Execution Context Discovery

**Goal**: Map all possible execution contexts where code can run.

**Execution contexts include**:
- Component lifecycle (mount, effects)
- Event handlers (onClick, onSubmit, etc.)
- Browser event listeners (scroll, resize)
- Timers & intervals
- Async callbacks
- State machine actions
- WebSocket message handlers
- Navigation triggers

**Output**: Map of execution contexts → call graphs

---

### Phase 7: Pattern Matching & Extraction

**Goal**: Find all network requests in the dependency tree with execution context.

**Steps**:
1. For each file, apply pattern matching for:
   - Built-in browser APIs (fetch, XMLHttpRequest, WebSocket)
   - HTTP client libraries
   - GraphQL queries
   - Third-party SDK calls
   - WebSockets

2. Link each request to its execution context
3. Note conditions and confidence levels

**Output**: Complete list of network request findings with context

---

### Phase 8: Categorize & Output

**Goal**: Present findings grouped by execution context.

**Categories**:
1. On Initial Load
2. On User Interaction
3. On Effects
4. On Timers/Polling
5. On Browser Events
6. On State Changes
7. On Navigation
8. Conditional/Unknown

Include performance metrics and save to specified file location.

## Limitations

Static analysis cannot detect:
- Requests from injected third-party scripts
- Exact runtime values for dynamic URLs
- Which conditional branches execute at runtime
- Server-side rendering requests
- External requests made by SDK internals

**Output is exhaustive but not deterministic**: Shows everything that COULD happen, not everything that WILL happen.
