# Docs next to code

Use this when you set up or maintain a docs folder or docs site in a repo. Do the setup steps only when the user asks for them.

## Layout

- Keep docs in the repo they describe, so a code change and its doc change land in one PR.
- Use one folder per mode: `docs/tutorials/`, `docs/how-to/`, `docs/reference/`, `docs/explanation/`. Mode specific Vale rules key off these folders.
- Generate reference from the source, such as `terraform-docs`, OpenAPI, or `--help`. Run the generator in pre-commit or CI so the reference can't drift.
- Link to the canonical upstream doc instead of copying it. Copied docs double the maintenance.
- Put `lastVerified: <YYYY-MM-DD>` in the frontmatter of runbooks and how-tos. Update it when someone runs every step.
- When you move or rename a page, add a redirect, and update every link to the old path.

## Make docs readable by agents

- Publish `llms.txt` at the site root, listing every page as Markdown links. See [llmstxt.org](https://llmstxt.org/).
- Serve a Markdown copy of each page, such as `<page>/index.md`. Markdown uses about 7 times fewer tokens than HTML.
- Keep content out of tabs and collapsed sections, or make sure it survives as labeled text in the Markdown copy.

To start a new docs site, consider [Nimbus](https://nimbus-docs.com/) (MIT, built on Astro). It ships page recipes, a docs linter, `llms.txt`, and Markdown copies.

## Set up the checks

Each repo owns its config, so that local runs and CI agree.

1. Add a `.vale.ini`. This config is tested against this skill's rules:

   ```ini
   StylesPath = .vale/styles
   MinAlertLevel = warning
   Packages = Google, proselint, Diataxis, AiTells, A11y

   [*.md]
   BasedOnStyles = Vale, Google, proselint, AiTells, A11y, Docs
   # Conflict with the docs skill or voice.md.
   Google.Quotes = NO
   # The author's voice uses first person.
   Google.FirstPerson = NO
   Google.We = NO
   Google.Colons = NO
   proselint.CurlyQuotes = NO
   # Contradicts Google.Ellipses, and duplicates Google's American spelling rule.
   proselint.Ellipsis = NO
   proselint.Spelling = NO
   # Weaker or duplicate versions of other rules.
   Google.EmDash = NO
   Google.Timeless = NO
   AiTells.Passive = NO
   AiTells.LinkText = NO
   # rumdl checks these.
   A11y.HeadingSkip = NO
   A11y.HeadingMultiple = NO
   A11y.LinkURL = NO
   # False positives: regex Oxford comma check misfires on "X, not Y", the skill says to
   # write real file names, Exclamation fires on GraphQL types, and WordListCase targets
   # mobile UI words like "touch".
   Google.OxfordComma = NO
   AiTells.FilePath = NO
   proselint.Exclamation = NO
   Google.WordListCase = NO
   # Docs.WordList replaces it, minus CLI and Cloud.
   Google.WordList = NO
   # The docs skill bans semicolons.
   Google.Semicolons = warning

   # A folder section replaces BasedOnStyles, so repeat the base styles.
   # Rule settings only take effect where the rule's style is enabled.
   [docs/tutorials/**/*.md]
   BasedOnStyles = Vale, Google, proselint, AiTells, A11y, Docs, Tutorial, DocsHowTo
   Google.We = YES
   Tutorial.We = NO
   Tutorial.Expectations = warning

   [docs/how-to/**/*.md]
   BasedOnStyles = Vale, Google, proselint, AiTells, A11y, Docs, HowTo, DocsHowTo
   Google.We = YES
   HowTo.Title = NO
   HowTo.Opening = NO
   HowTo.Imperative = warning
   HowTo.Explanation = warning

   [docs/reference/**/*.md]
   BasedOnStyles = Vale, Google, proselint, AiTells, A11y, Docs, Reference, DocsReference
   Google.We = YES

   [docs/explanation/**/*.md]
   BasedOnStyles = Vale, Google, proselint, AiTells, A11y, Docs, Explanation
   Explanation.Why = warning

   [docs/**/troubleshooting*.md]
   BasedOnStyles = Vale, Google, proselint, AiTells, A11y, Docs, DocsTroubleshooting
   ```

   Change the globs to match the repo's layout.

2. Copy the `Docs`, `DocsHowTo`, `DocsTroubleshooting`, and `DocsReference` folders from this skill's `vale/` folder to `.vale/styles/`.

3. Add `.vale/styles/*` to `.gitignore`, then add back `!.vale/styles/Docs*/` and `!.vale/styles/config/`. Synced packages stay out of git, and your own rules stay in.

4. Keep the project vocabulary in `.vale/styles/config/vocabularies/<Name>/accept.txt`, and set `Vocab = <Name>` under `[*.md]` and each folder section. Vale enforces the case of each accepted term, so prefix lowercase tool names with `(?i)`. Otherwise `aws` flags every `AWS`.

5. Add a `lychee.toml` with URL exclusions and accepted status codes.

6. Add the hooks to `.pre-commit-config.yaml`. `oxfmt` formats Markdown, YAML, and JSON in place of Prettier. `oxlint` only lints JavaScript and TypeScript, so it doesn't apply to docs. If pre-commit fails to install Node, add `default_language_version: {node: system}` to use the local Node.

   ```yaml
   - repo: https://github.com/oxc-project/mirrors-oxfmt
     rev: v0.79.0
     hooks:
       - id: oxfmt
         types_or: [markdown, yaml, json]
   - repo: https://github.com/vale-cli/vale
     rev: v3.28.1
     hooks:
       - id: vale
         args: [--no-global]
         types_or: [markdown, rst]
   - repo: https://github.com/lycheeverse/lychee
     rev: lychee-v0.24.2
     hooks:
       - id: lychee
         args: [--offline, --include-fragments, --no-progress]
         types_or: [markdown, rst]
   ```

7. In CI, run `vale sync` before the hooks. Check external URLs in a separate scheduled or PR job with `lycheeverse/lychee-action`, because network checks fail for reasons unrelated to the commit.

## What the config checks

| Style                                           | Where             | Checks                                                                                                                                            |
| ----------------------------------------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Google`                                        | All               | Google developer style, minus the rules that conflict with this skill                                                                             |
| `proselint`                                     | All               | Clichés, redundancy, and typography                                                                                                               |
| `AiTells`                                       | All               | AI-writing tells, including em and en dashes                                                                                                      |
| `A11y`                                          | All               | Alt text, generic link text, and sensory language                                                                                                 |
| `Docs`                                          | All               | Dated words, positional references, vague values, long step lists, hyphenated prose, the author's short forms, and Google's word list without CLI |
| `Tutorial`, `HowTo`, `Reference`, `Explanation` | Their folder      | Diátaxis: each page sticks to its mode                                                                                                            |
| `DocsHowTo`                                     | How-to, tutorials | Has a Verify section, ends with Next steps                                                                                                        |
| `DocsTroubleshooting`                           | Troubleshooting   | Each entry has bold Cause and Fix labels                                                                                                          |
| `DocsReference`                                 | Reference         | Each entry starts with (Required) or (Optional)                                                                                                   |

`rumdl` covers heading levels, code block languages, bare URLs, and `$` prompts, so the config turns off the A11y rules that repeat them.
