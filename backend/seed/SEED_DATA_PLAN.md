# Seed data policy

ROOT ACCESS is for players familiar with introductory computer science or
day-to-day programming. Prompts start with the idea the player recognizes,
such as “Name a programming language,” “Name a data structure,” or “Name an
HTTP status code.” Catalog details go in the scope below the prompt. A
reference can define the complete answer set, but a player should be able to
think of several valid answers without consulting it. Use named concepts,
tools, techniques, and features that readers may recall at different rates.
For HTTP response statuses, use the reason phrase as the answer.

## Answers and scoring

- `curated_questions.json` is the 100-question playable bank.
  `questions.json` retains the starter prompts used in development.
- Include all answers within the displayed catalog or rule. Let the size of
  that set vary by question. Use names and their common aliases.
- Each answer stores its canonical spelling, aliases, points, tier, source
  URL, and license or provenance. Equivalent names that clearly denote one
  answer share a score. Case-sensitive prompts preserve meaningful case.
- The five lower tiers each have multiple answers. Every prompt has exactly
  one Root Key. Put familiar answers in the lower tiers. Treat tier scores
  as editorial estimates until there is play data to calibrate them.

## Sources and regeneration

[The manifest](source_manifest.json) records the exact inputs and SHA-256
checksums. The generator preserves matching catalog entries and checks the
snapshot bytes before building. Keep those snapshots for repeatable
regeneration. Python-specific built-in names come from the Python 3.12
interpreter.

Key references include [GitHub Linguist](https://github.com/github-linguist/linguist),
the [NIST Dictionary of Algorithms and Data Structures](https://xlinux.nist.gov/dads/),
[DB-Engines](https://db-engines.com/en/ranking),
[MDN Browser Compatibility Data](https://github.com/mdn/browser-compat-data),
[SQLite](https://www.sqlite.org/lang.html), [Python](https://docs.python.org/3.12/),
[IANA](https://www.iana.org/protocols), [SPDX](https://spdx.org/licenses/),
the [CNCF Landscape](https://landscape.cncf.io/), and
[Awesome Selfhosted](https://github.com/awesome-selfhosted/awesome-selfhosted).

From `backend/`, with the Python 3.12 application environment active:

```sh
python -m pip install PyYAML==6.0.3
python seed/build_curated_bank.py /path/to/saved-snapshots
```

Use `--fetch` to fetch missing snapshots when the original bytes are still
available, and `--inspect` to review prompt wording and complete set sizes.

## Publishing

```sh
flask --app run.py db upgrade
flask --app run.py seed --bank curated
```

The importer validates scores, tier counts, normalized answer and alias
uniqueness, scopes, and provenance before writing. Seeding the curated bank
retires superseded managed questions from new draws. It retains the
questions and data for current and past dailies and for recorded runs.
Earlier previews of future dates are refreshed if they included a retired
question and have no runs. Dailies reset at 00:00 UTC.
