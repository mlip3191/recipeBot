import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import func  # noqa: E402
from sqlmodel import Session, select  # noqa: E402

from app.db import create_db_and_tables, engine  # noqa: E402
from app.models import Ingredient, Instruction, Protein, Recipe, Tag  # noqa: E402

REQUIRED_RECIPE_FIELDS = [
    "name",
    "protein_id",
    "genre",
    "cook_time_min",
    "total_time_min",
    "servings",
]


def validate_recipe_data(data: dict) -> None:
    missing = [field for field in REQUIRED_RECIPE_FIELDS if field not in data]
    if missing:
        raise ValueError(f"missing required field(s): {', '.join(missing)}")
    for ingredient in data.get("ingredients", []):
        if "item" not in ingredient:
            raise ValueError("an ingredient is missing 'item'")
    for instruction in data.get("instructions", []):
        if "text" not in instruction:
            raise ValueError("an instruction is missing 'text'")


def resolve_tags(session: Session, tag_names: list[str]) -> list[Tag]:
    tags = []
    for tag_name in tag_names:
        name = tag_name.strip()
        if not name:
            continue
        tag = session.exec(
            select(Tag).where(func.lower(Tag.name) == name.lower())
        ).first()
        if tag is None:
            tag = Tag(name=name)
            session.add(tag)
            session.flush()
        tags.append(tag)
    return tags


def upsert_recipe(session: Session, data: dict) -> str:
    validate_recipe_data(data)

    protein_id = data["protein_id"]
    if session.get(Protein, protein_id) is None:
        raise ValueError(f"protein_id {protein_id} does not exist")

    existing = session.exec(select(Recipe).where(Recipe.name == data["name"])).first()

    if existing is None:
        recipe = Recipe(
            name=data["name"],
            protein_id=protein_id,
            genre=data["genre"],
            cook_time_min=data["cook_time_min"],
            total_time_min=data["total_time_min"],
            servings=data["servings"],
            source=data.get("source"),
            notes=data.get("notes"),
        )
        session.add(recipe)
        session.flush()
        action = "created"
    else:
        recipe = existing
        recipe.protein_id = protein_id
        recipe.genre = data["genre"]
        recipe.cook_time_min = data["cook_time_min"]
        recipe.total_time_min = data["total_time_min"]
        recipe.servings = data["servings"]
        recipe.source = data.get("source")
        recipe.notes = data.get("notes")
        session.add(recipe)

        for ingredient in list(recipe.ingredients):
            session.delete(ingredient)
        for instruction in list(recipe.instructions):
            session.delete(instruction)
        session.flush()
        action = "updated"

    for index, ingredient in enumerate(data.get("ingredients", []), start=1):
        session.add(
            Ingredient(
                recipe_id=recipe.id,
                position=ingredient.get("position") or index,
                quantity=ingredient.get("quantity"),
                unit=ingredient.get("unit"),
                item=ingredient["item"],
                prep_note=ingredient.get("prep_note"),
            )
        )

    for index, instruction in enumerate(data.get("instructions", []), start=1):
        session.add(
            Instruction(
                recipe_id=recipe.id,
                step_number=instruction.get("step_number") or index,
                text=instruction["text"],
            )
        )

    recipe.tags = resolve_tags(session, data.get("tags", []))

    return action


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import recipes from a JSON file, upserting by name."
    )
    parser.add_argument("file", type=Path, help="Path to a JSON file with an array of recipes.")
    args = parser.parse_args()

    recipes = json.loads(args.file.read_text())
    if not isinstance(recipes, list):
        raise SystemExit("Expected a JSON array of recipes.")

    create_db_and_tables()

    created = 0
    updated = 0
    skipped = 0

    with Session(engine) as session:
        for data in recipes:
            try:
                action = upsert_recipe(session, data)
            except (KeyError, ValueError) as error:
                print(f"Skipping {data.get('name', '<unknown>')!r}: {error}")
                skipped += 1
                continue
            if action == "created":
                created += 1
            else:
                updated += 1
        session.commit()

    print(
        f"Imported {created + updated} recipes "
        f"({created} created, {updated} updated, {skipped} skipped)."
    )


if __name__ == "__main__":
    main()
