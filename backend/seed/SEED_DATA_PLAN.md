# Seed data policy

ROOT ACCESS uses original prompts and complete answer sets within explicitly
stated scopes. A daily has seven prompts and resets at 00:00 UTC.

## Question bank

- `questions.json` retains the 14 development prompts.
- `curated_questions.json` is the 100-question playable bank. Each prompt has
  at least 100 canonical answers. A scope names a reference version, a pinned
  catalog snapshot, or an exact enumerable rule. The game displays the scope
  with the prompt. It preserves every matching entry from that scope.
- Each answer stores its canonical spelling, accepted aliases, points, tier,
  source URL, and license or provenance. Typed aliases come from the source
  or unambiguous shorthand permitted by the question. Use qualified names
  when different APIs share a short name. Case-sensitive prompts such as the
  Base64 question keep distinct encodings separate and require exact matches.
- Public (10), Known Trick (15), User Space (30), Privileged (60), and Kernel
  (85) each have multiple answers. Every prompt has exactly one Root Key (100).
  Familiarity anchors and featured picks are editorial. The generator uses a
  deterministic ordering for the other entries. Treat these tiers as
  provisional until play data can support calibration.

## Sources and regeneration

[The manifest](source_manifest.json) records the exact input URLs and SHA-256
checksums. Moving catalogs are frozen by the checksum of the bytes used to
build this edition. The generator selects all matching records and never
caps an answer set. It refuses to rebuild from bytes that differ from the
manifest. Keep the snapshots for repeatable regeneration.

Primary references include [MDN Browser Compatibility Data](https://github.com/mdn/browser-compat-data),
[Python 3.12](https://docs.python.org/3.12/),
[Java 21](https://docs.oracle.com/en/java/javase/21/docs/api/allclasses-index.html),
[Node.js 22.16](https://nodejs.org/dist/v22.16.0/docs/api/),
[IANA](https://www.iana.org/protocols),
[Unicode 17](https://www.unicode.org/Public/17.0.0/ucd/),
[Debian 13](https://www.debian.org/releases/trixie/),
[SPDX](https://spdx.org/licenses/), and the other entries in the manifest.
Can I Use feature names are drawn from [Fyrd/caniuse](https://github.com/Fyrd/caniuse)
under CC BY 4.0. This bank groups those feature identifiers into new prompts.
See the [Unicode data notice](UNICODE-LICENSE.txt) for the Unicode-derived sets.

From `backend/`, with the application environment active, install PyYAML for
the generator and rebuild against the saved snapshots.

```sh
python -m pip install PyYAML==6.0.3
python seed/build_curated_bank.py /path/to/saved-snapshots
```

Use `--fetch` to download missing snapshots when the original bytes are
still available. Use `--inspect` to list complete set sizes. A seed or a
normal server start uses the generated JSON on disk.

## Publishing

```sh
flask --app run.py db upgrade
flask --app run.py seed --bank curated
```

The curated seed is the default. It validates the tier and score rules,
normalized answer and alias uniqueness, scope, and provenance before writing.
The starter set is available with `--bank starter` for development. Loading
the curated bank retires the starter prompts from future selections. Materialized
dailies keep their assigned prompts. The importer skips edits to questions in
the current UTC daily and keeps history-linked answer rows when retiring them.
