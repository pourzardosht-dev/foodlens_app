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
    recognition_hints: str
    kcal_per_100g: float
    uncertainty_percent: float
    portions: tuple[PortionUnit, ...]


FOODS: tuple[FoodProfile, ...] = (
    FoodProfile(
        id="ghormeh-sabzi",
        name_fa="قرمه‌سبزی",
        name_en="Ghormeh Sabzi",
        recognition_hints=(
            "dark green herb stew, usually with kidney beans, meat chunks and "
            "dried lime; no visible egg"
        ),
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
        recognition_hints="thick brown walnut and pomegranate stew, usually with poultry",
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
        recognition_hints="separate cooked rice grains, white or saffron colored",
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
        recognition_hints="long grilled minced-meat kebab, commonly served on a skewer",
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
        recognition_hints=(
            "thick herb and noodle soup with legumes, often topped with kashk and fried onion"
        ),
        kcal_per_100g=110,
        uncertainty_percent=20,
        portions=(
            PortionUnit("ladle", "ملاقه", 180),
            PortionUnit("bowl", "کاسه متوسط", 400),
        ),
    ),
    FoodProfile(
        id="baghala-ghatogh",
        name_fa="باقلاقاتق",
        name_en="Baghala Ghatogh",
        recognition_hints=(
            "light green or yellow Gilaki broad-bean and dill stew with one or more "
            "visible whole eggs; not a dark herb stew"
        ),
        kcal_per_100g=150,
        uncertainty_percent=25,
        portions=(
            PortionUnit("tablespoon", "قاشق غذاخوری", 25),
            PortionUnit("ladle", "ملاقه", 180),
            PortionUnit("bowl", "کاسه متوسط", 360),
        ),
    ),
    FoodProfile(
        id="anarbij",
        name_fa="اناربیج",
        name_en="Anarbij",
        recognition_hints=(
            "dark green-brown Gilaki walnut, pomegranate and herb stew, often with small "
            "meatballs; typically no kidney beans or dried lime"
        ),
        kcal_per_100g=210,
        uncertainty_percent=25,
        portions=(
            PortionUnit("tablespoon", "قاشق غذاخوری", 25),
            PortionUnit("ladle", "ملاقه", 180),
            PortionUnit("bowl", "کاسه متوسط", 360),
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
