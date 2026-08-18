import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import Session, select  # noqa: E402

from app.db import engine  # noqa: E402
from app.models import Recipe  # noqa: E402


def recipe_to_dict(recipe: Recipe) -> dict:
    return {
        "name": recipe.name,
        "protein_id": recipe.protein_id,
        "genre": recipe.genre,
        "cook_time_min": recipe.cook_time_min,
        "total_time_min": recipe.total_time_min,
        "servings": recipe.servings,
        "source": recipe.source,
        "notes": recipe.notes,
        "ingredients": [
            {
                "position": ingredient.position,
                "quantity": ingredient.quantity,
                "unit": ingredient.unit,
                "item": ingredient.item,
                "prep_note": ingredient.prep_note,
            }
            for ingredient in recipe.ingredients
        ],
        "instructions": [
            {"step_number": instruction.step_number, "text": instruction.text}
            for instruction in recipe.instructions
        ],
        "tags": [tag.name for tag in recipe.tags],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export all recipes to a JSON file.")
    parser.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Output path, or '-' for stdout (default).",
    )
    args = parser.parse_args()

    with Session(engine) as session:
        recipes = session.exec(select(Recipe).order_by(Recipe.name)).all()
        data = [recipe_to_dict(recipe) for recipe in recipes]

    output = json.dumps(data, indent=2)

    if args.file == "-":
        print(output)
    else:
        Path(args.file).write_text(output + "\n")
        print(f"Exported {len(data)} recipes to {args.file}")


if __name__ == "__main__":
    main()
