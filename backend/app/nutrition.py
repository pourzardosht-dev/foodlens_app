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
    default_portion_id: str
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
        default_portion_id="ladle",
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
        default_portion_id="ladle",
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
        default_portion_id="scoop",
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
        default_portion_id="skewer",
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
        default_portion_id="bowl",
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
        default_portion_id="ladle",
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
        default_portion_id="ladle",
        portions=(
            PortionUnit("tablespoon", "قاشق غذاخوری", 25),
            PortionUnit("ladle", "ملاقه", 180),
            PortionUnit("bowl", "کاسه متوسط", 360),
        ),
    ),
    FoodProfile(
        id="gheimeh",
        name_fa="خورش قیمه",
        name_en="Gheimeh",
        recognition_hints=(
            "yellow-orange split-pea and meat stew topped with thin fried potato sticks; "
            "no eggplant"
        ),
        kcal_per_100g=180,
        uncertainty_percent=22,
        default_portion_id="ladle",
        portions=(
            PortionUnit("tablespoon", "قاشق غذاخوری", 25),
            PortionUnit("ladle", "ملاقه", 180),
            PortionUnit("bowl", "کاسه متوسط", 360),
        ),
    ),
    FoodProfile(
        id="gheimeh-bademjan",
        name_fa="قیمه بادمجان",
        name_en="Gheimeh Bademjan",
        recognition_hints=(
            "split-pea tomato stew with prominent whole or sliced fried eggplants, "
            "usually without potato sticks"
        ),
        kcal_per_100g=175,
        uncertainty_percent=25,
        default_portion_id="ladle",
        portions=(
            PortionUnit("tablespoon", "قاشق غذاخوری", 25),
            PortionUnit("ladle", "ملاقه", 180),
            PortionUnit("bowl", "کاسه متوسط", 360),
        ),
    ),
    FoodProfile(
        id="khoresh-karafs",
        name_fa="خورش کرفس",
        name_en="Khoresh Karafs",
        recognition_hints=(
            "green herb stew with clearly visible pale celery stalk pieces and meat; "
            "typically no kidney beans or dried lime"
        ),
        kcal_per_100g=145,
        uncertainty_percent=22,
        default_portion_id="ladle",
        portions=(
            PortionUnit("tablespoon", "قاشق غذاخوری", 25),
            PortionUnit("ladle", "ملاقه", 180),
            PortionUnit("bowl", "کاسه متوسط", 360),
        ),
    ),
    FoodProfile(
        id="zereshk-polo-morgh",
        name_fa="زرشک‌پلو با مرغ",
        name_en="Zereshk Polo ba Morgh",
        recognition_hints=(
            "white or saffron rice scattered with red barberries, served with a distinct "
            "braised or roasted chicken piece"
        ),
        kcal_per_100g=190,
        uncertainty_percent=25,
        default_portion_id="plate",
        portions=(
            PortionUnit("half-plate", "نصف بشقاب", 250),
            PortionUnit("plate", "بشقاب متوسط", 500),
        ),
    ),
    FoodProfile(
        id="loobia-polo",
        name_fa="لوبیاپلو",
        name_en="Loobia Polo",
        recognition_hints=(
            "tomato-colored mixed rice with visible chopped green beans and often small "
            "pieces of meat"
        ),
        kcal_per_100g=170,
        uncertainty_percent=20,
        default_portion_id="plate",
        portions=(
            PortionUnit("scoop", "کفگیر", 110),
            PortionUnit("plate", "بشقاب متوسط", 330),
        ),
    ),
    FoodProfile(
        id="adas-polo",
        name_fa="عدس‌پلو",
        name_en="Adas Polo",
        recognition_hints=(
            "rice mixed with many small brown lentils, often topped with raisins, dates "
            "or minced meat; no chopped green beans"
        ),
        kcal_per_100g=170,
        uncertainty_percent=22,
        default_portion_id="plate",
        portions=(
            PortionUnit("scoop", "کفگیر", 110),
            PortionUnit("plate", "بشقاب متوسط", 330),
        ),
    ),
    FoodProfile(
        id="sabzi-polo-mahi",
        name_fa="سبزی‌پلو با ماهی",
        name_en="Sabzi Polo ba Mahi",
        recognition_hints=(
            "green herb-flecked rice served with a clearly visible whole fish or fish fillet"
        ),
        kcal_per_100g=180,
        uncertainty_percent=25,
        default_portion_id="plate",
        portions=(
            PortionUnit("half-plate", "نصف بشقاب", 250),
            PortionUnit("plate", "بشقاب متوسط", 500),
        ),
    ),
    FoodProfile(
        id="joojeh-kebab",
        name_fa="جوجه‌کباب",
        name_en="Joojeh Kebab",
        recognition_hints=(
            "chunks of yellow saffron-marinated grilled chicken, commonly threaded on a skewer"
        ),
        kcal_per_100g=190,
        uncertainty_percent=18,
        default_portion_id="skewer",
        portions=(
            PortionUnit("half-skewer", "نصف سیخ", 75),
            PortionUnit("skewer", "یک سیخ", 150),
        ),
    ),
    FoodProfile(
        id="kabab-barg",
        name_fa="کباب برگ",
        name_en="Kabab Barg",
        recognition_hints=(
            "flat wide strips of grilled beef or lamb on a skewer, not cylindrical minced meat"
        ),
        kcal_per_100g=230,
        uncertainty_percent=18,
        default_portion_id="skewer",
        portions=(
            PortionUnit("half-skewer", "نصف سیخ", 70),
            PortionUnit("skewer", "یک سیخ", 140),
        ),
    ),
    FoodProfile(
        id="abgoosht",
        name_fa="آبگوشت یا دیزی",
        name_en="Abgoosht",
        recognition_hints=(
            "brothy chickpea, bean, potato and meat dish, often served in a stone crock; "
            "may be separated into broth and mashed solids"
        ),
        kcal_per_100g=150,
        uncertainty_percent=28,
        default_portion_id="bowl",
        portions=(
            PortionUnit("ladle", "ملاقه", 180),
            PortionUnit("bowl", "کاسه متوسط", 450),
            PortionUnit("dizi", "یک دیزی", 650),
        ),
    ),
    FoodProfile(
        id="iranian-macaroni",
        name_fa="ماکارونی ایرانی",
        name_en="Iranian Macaroni",
        recognition_hints=(
            "tomato-coated spaghetti strands mixed with minced meat, sometimes potato tahdig; "
            "not rice"
        ),
        kcal_per_100g=175,
        uncertainty_percent=20,
        default_portion_id="plate",
        portions=(
            PortionUnit("scoop", "کفگیر", 120),
            PortionUnit("plate", "بشقاب متوسط", 350),
        ),
    ),
    FoodProfile(
        id="tahchin-morgh",
        name_fa="ته‌چین مرغ",
        name_en="Tahchin Morgh",
        recognition_hints=(
            "firm molded saffron-yellow baked rice cake with a browned crust and chicken layers"
        ),
        kcal_per_100g=210,
        uncertainty_percent=22,
        default_portion_id="slice",
        portions=(
            PortionUnit("half-slice", "نصف برش", 125),
            PortionUnit("slice", "یک برش", 250),
        ),
    ),
    FoodProfile(
        id="kashk-bademjan",
        name_fa="کشک بادمجان",
        name_en="Kashk Bademjan",
        recognition_hints=(
            "mashed brown eggplant dip topped with white kashk, fried mint and fried onions; "
            "no visible tomato or whole eggs"
        ),
        kcal_per_100g=180,
        uncertainty_percent=25,
        default_portion_id="bowl",
        portions=(
            PortionUnit("tablespoon", "قاشق غذاخوری", 25),
            PortionUnit("bowl", "کاسه کوچک", 250),
        ),
    ),
    FoodProfile(
        id="mirza-ghasemi",
        name_fa="میرزا قاسمی",
        name_en="Mirza Ghasemi",
        recognition_hints=(
            "smoky mashed eggplant with obvious red tomato and scrambled or set egg, "
            "usually orange-brown rather than green"
        ),
        kcal_per_100g=110,
        uncertainty_percent=22,
        default_portion_id="bowl",
        portions=(
            PortionUnit("tablespoon", "قاشق غذاخوری", 25),
            PortionUnit("bowl", "کاسه کوچک", 250),
        ),
    ),
    FoodProfile(
        id="kookoo-sabzi",
        name_fa="کوکو سبزی",
        name_en="Kookoo Sabzi",
        recognition_hints=(
            "dark green pan-fried herb and egg cake cut into wedges or rectangles; "
            "not a liquid stew"
        ),
        kcal_per_100g=200,
        uncertainty_percent=20,
        default_portion_id="piece",
        portions=(
            PortionUnit("half-piece", "نصف تکه", 50),
            PortionUnit("piece", "یک تکه", 100),
        ),
    ),
    FoodProfile(
        id="kotlet",
        name_fa="کتلت",
        name_en="Kotlet",
        recognition_hints=(
            "flat oval or round browned fried patties made from potato and minced meat; "
            "brown inside rather than bright green"
        ),
        kcal_per_100g=230,
        uncertainty_percent=22,
        default_portion_id="piece",
        portions=(
            PortionUnit("half-piece", "نصف عدد", 45),
            PortionUnit("piece", "یک عدد", 90),
        ),
    ),
    FoodProfile(
        id="dolmeh-barg-mo",
        name_fa="دلمه برگ مو",
        name_en="Dolmeh Barg Mo",
        recognition_hints=(
            "small tightly rolled or folded grape leaves stuffed with rice and herbs"
        ),
        kcal_per_100g=160,
        uncertainty_percent=22,
        default_portion_id="piece",
        portions=(
            PortionUnit("piece", "یک عدد", 35),
            PortionUnit("five-pieces", "پنج عدد", 175),
        ),
    ),
    FoodProfile(
        id="koofteh-tabrizi",
        name_fa="کوفته تبریزی",
        name_en="Koofteh Tabrizi",
        recognition_hints=(
            "one or more very large round meat, rice and herb balls served in tomato broth; "
            "much larger than Anarbij meatballs"
        ),
        kcal_per_100g=190,
        uncertainty_percent=25,
        default_portion_id="piece",
        portions=(
            PortionUnit("half-piece", "نصف عدد", 175),
            PortionUnit("piece", "یک عدد", 350),
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
