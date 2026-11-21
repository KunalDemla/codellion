import click
from app import create_app
from app.seed import seed_questions

app = create_app()

@app.cli.command("seed")
def seed_command():
    """Load or update curated question data (safe to run repeatedly)."""
    with app.app_context():
        seed_questions()
    click.echo("Seed data loaded.")
