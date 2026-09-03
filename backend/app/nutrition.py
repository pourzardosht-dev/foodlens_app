from dataclasses import dataclass


@dataclass(frozen=True)
class PortionUnit:
    id: str
    name_fa: str
    grams: float


@dataclass(frozen=True)
class FoodProfile:
    id: str
    name_fa: str
    name_en: str
    kcal_per_100g: float
    uncertainty_percent: float
    portions: tuple[PortionUnit, ...]


FOODS: tuple[FoodProfile, ...] = (
    FoodProfile(
        id="ghormeh-sabzi",
        name_fa="قرمه‌سبزی",
        name_en="Ghormeh Sabzi",
        kcal_per_100g=165,
        uncertainty_percent=18,
        portions=(
            PortionUnit("tablespoon", "قاشق غذاخوری", 25),
            PortionUnit("ladle", "ملاقه", 180),
            PortionUnit("bowl", "کاسه متوسط", 360),
        ),
    ),
    FoodProfile(
        id="fesenjan",
        name_fa="فسنجان",
        name_en="Fesenjan",
        kcal_per_100g=220,
        uncertainty_percent=22,
        portions=(
            PortionUnit("tablespoon", "قاشق غذاخوری", 25),
            PortionUnit("ladle", "ملاقه", 180),
            PortionUnit("bowl", "کاسه متوسط", 360),
        ),
    ),
    FoodProfile(
        id="cooked-rice",
        name_fa="برنج پخته",
        name_en="Cooked Rice",
        kcal_per_100g=130,
        uncertainty_percent=10,
        portions=(
            PortionUnit("tablespoon", "قاشق غذاخوری", 18),
            PortionUnit("scoop", "کفگیر", 110),
            PortionUnit("plate", "بشقاب متوسط", 330),
        ),
    ),
    FoodProfile(
        id="koobideh-kebab",
        name_fa="کباب کوبیده",
        name_en="Koobideh Kebab",
        kcal_per_100g=250,
        uncertainty_percent=15,
        portions=(
            PortionUnit("half-skewer", "نصف سیخ", 50),
            PortionUnit("skewer", "یک سیخ", 100),
        ),
    ),
    FoodProfile(
        id="ash-reshteh",
        name_fa="آش رشته",
        name_en="Ash Reshteh",
        kcal_per_100g=110,
        uncertainty_percent=20,
        portions=(
            PortionUnit("ladle", "ملاقه", 180),
            PortionUnit("bowl", "کاسه متوسط", 400),
        ),
    ),
)


def get_food(food_id: str) -> FoodProfile:
    for food in FOODS:
        if food.id == food_id:
            return food
    raise KeyError(food_id)


def estimate_calories(
    food: FoodProfile, portion: PortionUnit, quantity: float
) -> tuple[float, float, float, float]:
    grams = portion.grams * quantity
    calories = grams * food.kcal_per_100g / 100
    uncertainty = calories * food.uncertainty_percent / 100
    return grams, calories, calories - uncertainty, calories + uncertainty
