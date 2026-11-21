---
name: research
description: Use when about to implement a new feature, to gather context from documentation, real world code examples, and web resources. Provides structured findings to inform implementation decisions.
version: 1.1.0
tags: [research, planning, mcp]
---

# Research

Gather context from documentation, real code, and the web before you implement a feature, so the plan rests on how the library and other projects actually work.

## When to use this skill

- Planning or implementing a new feature. Use it by default.
- Working with a library or framework you don't know well.
- Weighing architectural approaches or design patterns.
- Seeing how others solved a similar problem.
- Choosing a technology.

## Process

Work through four phases in order:

1. Ask the user about requirements and sources.
2. Query the official docs with the context7 MCP server.
3. Find real code with the grep MCP server (`searchGitHub`).
4. Optionally, fetch web pages with `webfetch`.

### 1. Ask the user

Before you research, ask:

- What are the requirements and constraints for this feature?
- Do you prefer any libraries or approaches?
- Which docs or sources should I read?
- What matters most: performance, simplicity, or maintainability?
- How well do you know this technology?

Note any links, examples, and experience the user shares.

### 2. Query the docs

Use the context7 MCP server:

1. Resolve the library ID for each package or framework.
2. Query the docs for the APIs, configuration, and recommended patterns.
3. Note version requirements and compatibility issues.
4. Stay on the feature you're building.

By default, run one query, aimed at the feature, against the docs for the library version the project uses.

```bash
# Resolve library ID
mcp-cli context7/resolve-library-id '{"query": "OAuth2 authentication", "libraryName": "golang.org/x/oauth2"}'

# Query documentation
mcp-cli context7/query-docs '{"libraryId": "/golang/oauth2", "query": "Google OAuth configuration and token handling"}'
```

### 3. Find real code

Use the grep MCP server's `searchGitHub`:

1. Search for literal code that would appear in a file.
2. Find common idioms and implementations that run in production.
3. Note what they do on errors and edge cases, such as retries, timeouts, and empty results.
4. Filter by language, repo, or path to narrow noisy results.

By default, run 1 or 2 searches: the main pattern, and its error handling. Prefer recent, maintained repos.

Search for code, not prose:

- Good: `oauth2.Config{`, `import "golang.org/x/oauth2"`, `TokenSource`
- Bad: `oauth tutorial`, `best practices`, `how to authenticate`

```bash
# Find main implementation pattern
mcp-cli grep/searchGitHub '{"query": "oauth2.Config{", "language": ["Go"]}'

# Find error handling pattern
mcp-cli grep/searchGitHub '{"query": "oauth2.TokenSource", "language": ["Go"]}'
```

### 4. Fetch web pages

Use `webfetch` for blog posts, tutorials, discussions, and other project docs. Fetch only when:

- The user already knows what they're looking for, and has links.
- The MCP sources are missing context you need.
- An architectural decision needs community experience.
- You need the tradeoffs between approaches.

Ask the user for links first. Fetch 1 or 2 pages, from official blogs and established docs, published in the last year.

```bash
# Fetch architectural guidance
webfetch https://cloud.google.com/docs/authentication
```

### When a source fails

If an MCP server or `webfetch` fails, keep going with the other sources:

1. Record the exact error.
2. Continue with the sources that work.
3. Tell the user what's missing.
4. State the assumptions you made because of it.

Use this message format:

```text
⚠️ MCP server '<server>' unavailable (<error, such as connection refused or timeout after 30s>) - proceeding with <alternative>
```

## Match depth to risk

| Scenario                | Depth      | Goal                                    | Queries                   |
| ----------------------- | ---------- | --------------------------------------- | ------------------------- |
| Well known pattern      | Minimal    | Confirm the recommended pattern         | 1 doc, 1 code             |
| Standard feature        | Quick scan | Confirm the common approaches           | 1 doc, 1-2 code           |
| New kind of feature     | Thorough   | Compare alternatives and tradeoffs      | 2-3 doc, 3-4 code         |
| Critical infrastructure | Deep       | Understand failure modes and edge cases | Several from every source |

Default to a quick scan of 2 to 3 minutes, aimed at the specific implementation questions. Most features don't need more, and a long search mostly turns up the same pattern again. Go deeper when the user doesn't know the technology, the feature is complex or new, the risk is high (security, data integrity, performance), or the codebase has no existing pattern to copy.

## Report the findings

Use this template:

```markdown
## Research summary: <feature>

### User context

- <Key requirements from the user>
- <Constraints or preferences>
- <Docs links the user gave>

### Common patterns

- <Pattern, with source>

### Tradeoffs

- Approach A: <pros, cons, when to use>
- Approach B: <pros, cons, when to use>
- Decisions needed: <what, and why>

### Recommendation

<The approach, and why it fits the research and the requirements>

### Implementation notes

- <A finding that changes the implementation>
- <A pitfall to avoid>
- <A configuration detail>
- <How to test it>

### Sources

- <Library docs page>
- <GitHub example: repo/file:line>
- <Blog post or guide>

### MCP status

✓ All sources available | ⚠️ <failure details>
```

Keep it short. Give the reason for each recommendation and link every source. When the sources disagree or run out, say so, and label your guess as a guess: "My best guess is…".

## Rules

- Ask the user questions before you start, and ask for doc links.
- Don't guess the requirements.
- Search for literal code, not prose.
- Prefer maintained, production examples, and check version compatibility.
- Report each MCP failure with its error. Don't hide it.
- Don't start implementing before the research is done, unless every source is down.

## Examples

### Adding OAuth authentication

Questions:

```text
Q: "Which OAuth provider are you planning to use?"
A: "Google OAuth, but open to suggestions"

Q: "Are there any specific documentation or libraries you prefer?"
A: "No preference, whatever is most reliable"

Q: "What are the key constraints (compliance, user experience)?"
A: "Need to be production-ready and secure"
```

Research:

1. Resolve the library ID for Go OAuth libraries: `golang.org/x/oauth2`.
2. Query context7: "Google OAuth configuration and token handling".
3. Search GitHub for `oauth2.Config{` with `language=["Go"]`.
4. Search GitHub for `oauth2.TokenSource` with `language=["Go"]`.

Findings:

- Most Go projects use `golang.org/x/oauth2`.
- The common pattern is middleware that validates the token.
- The code has to refresh tokens before they expire.
- Check the token before each request.
- Store credentials in environment variables.

Recommendation: use the `golang.org/x/oauth2/google` package with middleware that validates tokens. It's the most common pattern in production Go apps, and it refreshes tokens for you.

### Adding rate limiting

Questions:

```text
Q: "What type of rate limiting do you need (per-user, per-IP, global)?"
A: "Per-user, based on API key"

Q: "What are your rate limit requirements?"
A: "100 requests per minute per user"

Q: "Do you need distributed rate limiting across multiple servers?"
A: "No, single server deployment"
```

Research:

1. Resolve the library ID for rate limiting: `golang.org/x/time/rate`.
2. Query context7 for "rate limiting configuration". The connection times out.
3. Search GitHub for `rate.NewLimiter` with `language=["Go"]`.
4. Search GitHub for `rate.Limiter.Allow` with `language=["Go"]`.

Findings:

- `⚠️ MCP server 'context7' unavailable (connection timeout after 30s) - proceeding with grep searches only`
- The common library is `golang.org/x/time/rate`.
- Projects keep one limiter per API key or user ID in a map.
- Middleware checks the limiter before the handler runs.
- One server can use an in memory map. Several servers need Redis.

Recommendation: use `golang.org/x/time/rate.NewLimiter(rate.Limit(100/60), 100)`, with a `sync.Map` that holds one limiter per user. It keeps rate limiting in memory, which fits a single server.

### Setting up a CI pipeline

Questions:

```text
Q: "Which CI/CD platform are you using?"
A: "GitHub Actions"

Q: "What should the pipeline do?"
A: "Run tests, linting, and build on every push"
```

Research:

1. Query context7: "GitHub Actions Go workflow configuration".
2. Search GitHub for `runs-on: ubuntu-latest` with `path=".github/workflows"` and `language=["YAML"]`.
3. Search GitHub for `go test ./...` with `path=".github/workflows"`.

Findings:

- Projects use a matrix build across Go versions.
- The usual steps are checkout, set up Go, cache dependencies, test, and build.
- Linters run before tests, so the pipeline fails fast.
- `actions/cache` caches Go modules.
- PRs and the main branch often get separate workflows.

Recommendation: use a GitHub Actions matrix for Go 1.21 and later. Run `golangci-lint` before the tests, and cache Go modules to speed up builds. Most open source Go projects do this.

## Use it in planning

1. Start with this skill.
2. Ask the user about requirements.
3. Ask for doc links.
4. Research the docs, then code, then the web.
5. Present the findings with a recommendation.
6. Get the user's approval on the approach.
7. Plan the implementation from the findings.

The findings should drive the choice of library, pattern, or framework, along with the architecture, error handling, edge cases, tests, and docs.
