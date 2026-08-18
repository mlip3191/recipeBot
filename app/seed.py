from sqlmodel import Session, select

from app.models import Ingredient, Instruction, Protein, Recipe, Tag

PROTEIN_NAMES = [
    "Chicken",
    "Beef",
    "Pork",
    "Fish",
    "Shellfish",
    "Lamb",
    "Turkey",
    "Vegetarian",
]

TAG_NAMES = [
    "smoker",
    "weeknight",
    "meal-prep",
    "one-pot",
    "grill",
    "kid-friendly",
    "make-ahead",
    "spicy",
]

SAMPLE_RECIPES = [
    {
        "name": "Simple Roast Chicken",
        "protein": "Chicken",
        "genre": "American",
        "cook_time_min": 75,
        "total_time_min": 90,
        "servings": 4,
        "source": "Family recipe",
        "notes": "Let rest 10 minutes before carving.",
        "tags": ["make-ahead"],
        "ingredients": [
            ("1", "whole", "chicken", "about 4-5 lbs"),
            ("2", "tbsp", "olive oil", None),
            ("1", "tsp", "salt", None),
            ("1", "tsp", "black pepper", None),
            ("1", "whole", "lemon", "halved"),
            ("4", "sprigs", "fresh thyme", None),
        ],
        "instructions": [
            "Preheat oven to 425F.",
            "Pat chicken dry and rub with olive oil.",
            "Season generously inside and out with salt and pepper.",
            "Stuff cavity with lemon halves and thyme sprigs.",
            "Roast for 75 minutes, until internal temp reaches 165F.",
            "Rest 10 minutes before carving.",
        ],
    },
    {
        "name": "Weeknight Beef Chili",
        "protein": "Beef",
        "genre": "American",
        "cook_time_min": 45,
        "total_time_min": 55,
        "servings": 6,
        "source": None,
        "notes": None,
        "tags": ["weeknight", "one-pot", "meal-prep"],
        "ingredients": [
            ("2", "lbs", "ground beef", None),
            ("1", "whole", "onion", "diced"),
            ("3", "cloves", "garlic", "minced"),
            ("2", "cans", "diced tomatoes", "14.5 oz each"),
            ("2", "cans", "kidney beans", "drained and rinsed"),
            ("2", "tbsp", "chili powder", None),
            ("1", "tsp", "cumin", None),
        ],
        "instructions": [
            "Brown ground beef in a large pot over medium-high heat.",
            "Add onion and garlic, cook until softened.",
            "Stir in tomatoes, beans, chili powder, and cumin.",
            "Simmer uncovered for 30 minutes, stirring occasionally.",
            "Taste and adjust seasoning before serving.",
        ],
    },
    {
        "name": "Pork Stir-Fry",
        "protein": "Pork",
        "genre": "Asian",
        "cook_time_min": 20,
        "total_time_min": 30,
        "servings": 4,
        "source": None,
        "notes": "Serve over steamed rice.",
        "tags": ["weeknight", "spicy"],
        "ingredients": [
            ("1", "lb", "pork tenderloin", "thinly sliced"),
            ("2", "tbsp", "soy sauce", None),
            ("1", "tbsp", "cornstarch", None),
            ("2", "tbsp", "vegetable oil", None),
            ("2", "cups", "mixed vegetables", "bell pepper, broccoli, carrot"),
            ("2", "cloves", "garlic", "minced"),
            ("1", "tbsp", "fresh ginger", "grated"),
        ],
        "instructions": [
            "Toss pork slices with soy sauce and cornstarch.",
            "Heat oil in a wok over high heat.",
            "Stir-fry pork until browned, about 3-4 minutes, then remove.",
            "Stir-fry vegetables, garlic, and ginger until crisp-tender.",
            "Return pork to the wok and toss to combine.",
            "Serve immediately over rice.",
        ],
    },
    {
        "name": "Grilled Salmon with Lemon",
        "protein": "Fish",
        "genre": "Mediterranean",
        "cook_time_min": 12,
        "total_time_min": 20,
        "servings": 2,
        "source": None,
        "notes": None,
        "tags": ["grill", "weeknight"],
        "ingredients": [
            ("2", "fillets", "salmon", "6 oz each"),
            ("1", "tbsp", "olive oil", None),
            ("1", "whole", "lemon", "sliced"),
            ("1", "tsp", "salt", None),
            ("0.5", "tsp", "black pepper", None),
            ("2", "sprigs", "fresh dill", None),
        ],
        "instructions": [
            "Preheat grill to medium-high heat.",
            "Brush salmon fillets with olive oil and season with salt and pepper.",
            "Grill skin-side down for 6-7 minutes.",
            "Flip and grill another 4-5 minutes until flaky.",
            "Top with lemon slices and fresh dill before serving.",
        ],
    },
    {
        "name": "Vegetarian Pasta Primavera",
        "protein": "Vegetarian",
        "genre": "Italian",
        "cook_time_min": 25,
        "total_time_min": 35,
        "servings": 4,
        "source": None,
        "notes": "Great with any seasonal vegetables.",
        "tags": ["weeknight", "kid-friendly"],
        "ingredients": [
            ("12", "oz", "pasta", None),
            ("2", "tbsp", "olive oil", None),
            ("1", "cup", "cherry tomatoes", "halved"),
            ("1", "cup", "zucchini", "sliced"),
            ("1", "cup", "broccoli florets", None),
            ("3", "cloves", "garlic", "minced"),
            ("0.5", "cup", "parmesan cheese", "grated"),
        ],
        "instructions": [
            "Cook pasta according to package directions; reserve 1 cup pasta water.",
            "Heat olive oil in a large skillet over medium heat.",
            "Saute garlic, zucchini, and broccoli until tender.",
            "Add cherry tomatoes and cook 2 more minutes.",
            "Toss in cooked pasta, adding pasta water as needed to loosen.",
            "Top with parmesan cheese and serve.",
        ],
    },
]


def seed_proteins(session: Session) -> None:
    existing = set(session.exec(select(Protein.name)).all())
    for name in PROTEIN_NAMES:
        if name not in existing:
            session.add(Protein(name=name))
    session.commit()


def seed_tags(session: Session) -> None:
    existing = set(session.exec(select(Tag.name)).all())
    for name in TAG_NAMES:
        if name not in existing:
            session.add(Tag(name=name))
    session.commit()


def seed_recipes(session: Session) -> None:
    if session.exec(select(Recipe.id).limit(1)).first() is not None:
        return

    proteins_by_name = {p.name: p for p in session.exec(select(Protein)).all()}
    tags_by_name = {t.name: t for t in session.exec(select(Tag)).all()}

    for recipe_data in SAMPLE_RECIPES:
        protein = proteins_by_name[recipe_data["protein"]]
        recipe = Recipe(
            name=recipe_data["name"],
            protein_id=protein.id,
            genre=recipe_data["genre"],
            cook_time_min=recipe_data["cook_time_min"],
            total_time_min=recipe_data["total_time_min"],
            servings=recipe_data["servings"],
            source=recipe_data["source"],
            notes=recipe_data["notes"],
            tags=[tags_by_name[name] for name in recipe_data.get("tags", [])],
        )
        session.add(recipe)
        session.flush()

        for position, (quantity, unit, item, prep_note) in enumerate(
            recipe_data["ingredients"], start=1
        ):
            session.add(
                Ingredient(
                    recipe_id=recipe.id,
                    position=position,
                    quantity=quantity,
                    unit=unit,
                    item=item,
                    prep_note=prep_note,
                )
            )

        for step_number, text in enumerate(recipe_data["instructions"], start=1):
            session.add(
                Instruction(
                    recipe_id=recipe.id,
                    step_number=step_number,
                    text=text,
                )
            )

    session.commit()


def seed(session: Session) -> None:
    seed_proteins(session)
    seed_tags(session)
    seed_recipes(session)
