import click
from app import create_app
from app.seed import seed_questions

app = create_app()

@app.cli.command("seed")
@click.option("--bank", type=click.Choice(["curated", "starter"]), default="curated", show_default=True)
def seed_command(bank):
    """Load or update curated question data (safe to run repeatedly)."""
    with app.app_context():
        seed_questions(bank)
    click.echo(f"Loaded {bank} seed data.")
