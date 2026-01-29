# Route Network Scanner - Design Documentation

## Overview

This skill analyzes a given URL route and traces all network requests made by that route and its nested components. It works with NX monorepos, standard JavaScript/TypeScript repos, and React applications with React Router.

## Installation

### Easy Installation (Recommended)

From the llm-hub repository directory, open Claude Code and ask:

```
"Please install the route-network-scanner skill globally from claude-plugins/skills/route-network-scanner"
```

Claude will automatically copy the skill files to `~/.claude/skills/route-network-scanner/` and confirm when it's ready to use.

### Manual Installation

If you prefer to install manually:

1. **Clone or download this repository**
   ```bash
   git clone https://github.com/allergan-data-labs/llm-hub.git
   cd llm-hub/claude-plugins/skills/route-network-scanner
   ```

2. **Create the global skills directory** (if it doesn't exist)
   ```bash
   mkdir -p ~/.claude/skills/route-network-scanner
   ```

3. **Copy the skill files**
   ```bash
   cp SKILL.md ~/.claude/skills/route-network-scanner/
   cp README.md ~/.claude/skills/route-network-scanner/
   ```

4. **Verify installation**
   ```bash
   ls -la ~/.claude/skills/route-network-scanner/
   # Should show SKILL.md and README.md
   ```

The skill is now available in all Claude Code sessions. You can invoke it with prompts like:
- "Analyze the /login route for network requests"
- "What network calls does the /dashboard route make?"
- "Scan the /checkout route for API dependencies"

## Scope of Network Requests

The skill identifies all types of network requests, categorized by execution context:

**By Execution Context:**
- **On Initial Load** - Requests from parent providers and route mount
- **On User Interaction** - Click handlers, form submissions, input changes
- **On Effects** - React useEffect/lifecycle triggers with dependencies
- **On Timers/Polling** - setTimeout, setInterval, requestAnimationFrame
- **On Browser Events** - Scroll, resize, visibility change listeners
- **On State Changes** - Redux/Zustand/Context actions
- **On Navigation** - Cleanup, tracking when leaving route
- **Conditional/Unknown** - Requests with unclear or multiple trigger paths

**By Request Type:**
- REST API calls (fetch, axios, ky, superagent, etc.)
- GraphQL queries/mutations/subscriptions
- Third-party SDK calls (Split.io, Contentful, Datadog, Sentry, Segment, Firebase, etc.)
- WebSocket connections and events
- Analytics and tracking calls
- Browser native APIs (XMLHttpRequest, fetch, EventSource)

## Analysis Approach: Static vs Runtime

### Static Analysis (Current Implementation)

**Advantages:**
- **No environment needed** - Works without running the app, setting up servers, auth, or databases
- **Complete coverage** - Finds ALL potential network requests in the code, even ones behind feature flags, A/B tests, or conditional logic you might not hit at runtime
- **Fast** - Can analyze entire route trees in seconds
- **Safe** - No risk of triggering real API calls, side effects, or affecting production data
- **Historical view** - Can see what requests existed at any point in git history

**Disadvantages:**
- **Conservative completeness** - Shows ALL possible requests (including those in conditional branches), which may include some that never execute
- **Dynamic requests** - Can detect patterns but won't show actual runtime values for template literals
- **Limited context** - Won't show actual payloads, headers, or response data
- **Third-party SDK internals** - Can't detect hidden requests made internally by third-party SDKs (treats them as black boxes)

### Runtime Analysis (Alternative Approach)

**Advantages:**
- **Ground truth** - Shows exactly what actually happens
- **Complete network picture** - Captures everything: third-party scripts, analytics, CDN requests
- **Real data** - See actual payloads, timing, headers, responses
- **Dynamic requests** - Catches all computed/interpolated URLs
- **Execution order** - Shows request waterfall and dependencies

**Disadvantages:**
- **Environment complexity** - Needs running app, backend services, authentication
- **Incomplete coverage** - Only sees the specific path you execute
- **State-dependent** - Different users/states may see different requests
- **Time-consuming** - Must manually navigate and interact
- **Reproducibility** - Hard to capture all edge cases consistently

### Hybrid Approach (Possible Future Enhancement)

The skill could potentially support both:

1. **Static analysis mode** (default) - Fast, comprehensive code scanning
2. **Runtime analysis mode** - Guide setup of browser recording with instructions to:
   - Open DevTools Network tab
   - Navigate to the route
   - Export HAR file
   - Parse and summarize the actual requests

## Common Use Cases

- **Documentation** - Document API dependencies for a route
- **Debugging** - Identify unexpected network calls
- **Security audits** - Audit all external requests
- **Performance analysis** - Understand request patterns and bottlenecks
- **Migration planning** - Identify all API dependencies before refactoring
- **Onboarding** - Help new developers understand data flow

## Implementation Approach

The skill performs **comprehensive execution context tracing** using only available tools (Read, Grep, Glob, Bash):

1. **Dynamic pattern discovery** - No hard-coded patterns; discovers network libraries and their usage patterns from package.json and actual code
2. **Bidirectional traversal** - Analyzes both parent components (providers, layouts) AND child dependencies
3. **Execution context mapping** - Traces ALL possible execution paths:
   - Component lifecycle (mount, effects, cleanup)
   - Event handlers (clicks, form submits, input changes)
   - Browser events (scroll, resize, visibility)
   - Timers and polling (setTimeout, setInterval)
   - State changes (Redux, Zustand, Context)
   - Navigation triggers (route changes, cleanup)
4. **Lazy loading support** - Detects and follows `ReactLazyPreload` and `React.lazy()` patterns
5. **React Router optimized** - Prioritizes routesConfig files for faster route resolution
6. **NX monorepo support** - Respects workspace boundaries and project structure
7. **Tool-based execution** - Uses ONLY provided tools (no custom scripts), ensuring reliable analysis

### Key Design Decisions

- **Pattern Re-discovery**: Always re-discover patterns on each run (no caching) to ensure accuracy as dependencies change
- **No depth limits**: Full traversal of application code regardless of nesting depth
- **Parent component analysis**: Simulates fresh page load by tracing component tree from route up to app root
- **Third-party boundaries**: Tracks application's usage of SDKs but doesn't traverse into node_modules
- **Conservative completeness**: Includes ALL possible requests (even in conditional branches) to avoid missing any potential network calls
- **Execution context priority**: Groups findings by WHEN/HOW they trigger, not just by what library they use
- **User prompts for output**: Asks user for output file location BEFORE starting analysis
- **Performance tracking**: Measures and reports execution time for each analysis phase

For detailed implementation instructions and the complete 8-phase analysis workflow, see SKILL.md.

## Future Enhancements

- Support for runtime HAR file analysis
- Integration with network monitoring tools
- Request dependency graph visualization
- Performance impact estimation
- Dead code detection (unused requests)
