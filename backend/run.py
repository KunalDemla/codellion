import click
from app import create_app
from app.seed import seed_questions

app = create_app()

@app.cli.command("seed")
def seed_command():
    with app.app_context():
        seed_questions()
        click.echo("Seed data loaded.")
