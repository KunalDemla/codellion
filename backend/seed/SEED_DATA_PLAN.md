# Seed data policy

The JSON file contains an initial bank of fourteen original development prompts with six manually curated answer tiers each. A daily uses a stable seven-prompt selection and resets at 00:00 UTC. Treat rarity tiers and points as provisional game-balancing values, not measured population statistics.

For a public question bank:
1. Write original prompts; do not copy quiz/question-bank wording from websites.
2. Gather candidate technical entities from public references (standards, official documentation, textbooks, or Wikidata where appropriate).
3. Verify each answer and alias against an authoritative source.
4. Store canonical answer, normalized aliases, source URL, and license/provenance metadata.
5. Review ambiguous answers manually; aliases must be scoped to the relevant question.
6. Keep exactly one answer in each tier: Public (10), Known Trick (15), User Space (30), Privileged (60), Kernel (85), and Root Key (100). Initially assign rarity editorially. Later calibrate from anonymized aggregate answer frequencies, with safeguards against small-sample noise and abuse.
7. Review the content and scoring before publishing. Do not assume the starter values are balanced.

The seed command validates seven-question coverage, six unique tiers per question, exact tier scores, and normalized canonical/alias uniqueness. It updates existing canonical answers and synchronizes aliases. Do not reseed or alter answer data during a live UTC daily; materialized daily sets retain prompt order, while the question bank supplies answer keys.
