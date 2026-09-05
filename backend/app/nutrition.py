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
        recognition_hints="separate plain cooked white rice grains without mixed ingredients",
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
        id="saffron-rice",
        name_fa="برنج زعفرانی",
        name_en="Saffron Rice",
        recognition_hints=(
            "a distinct serving of uniformly yellow saffron rice; do not classify a small "
            "yellow garnish on white rice as a separate component"
        ),
        kcal_per_100g=145,
        uncertainty_percent=15,
        default_portion_id="scoop",
        portions=(
            PortionUnit("tablespoon", "قاشق غذاخوری", 18),
            PortionUnit("scoop", "کفگیر", 110),
            PortionUnit("plate", "بشقاب متوسط", 330),
        ),
    ),
    FoodProfile(
        id="rice-tahdig",
        name_fa="ته‌دیگ برنج",
        name_en="Rice Tahdig",
        recognition_hints="crisp golden-brown compact rice crust with visible fused rice grains",
        kcal_per_100g=280,
        uncertainty_percent=25,
        default_portion_id="piece",
        portions=(
            PortionUnit("small-piece", "تکه کوچک", 35),
            PortionUnit("piece", "یک تکه", 70),
        ),
    ),
    FoodProfile(
        id="bread-tahdig",
        name_fa="ته‌دیگ نان",
        name_en="Bread Tahdig",
        recognition_hints=(
            "thin crisp golden fried flatbread sheet or shard from the bottom of a rice pot; "
            "no fused rice grains"
        ),
        kcal_per_100g=330,
        uncertainty_percent=28,
        default_portion_id="piece",
        portions=(
            PortionUnit("small-piece", "تکه کوچک", 25),
            PortionUnit("piece", "یک تکه", 50),
        ),
    ),
    FoodProfile(
        id="potato-tahdig",
        name_fa="ته‌دیگ سیب‌زمینی",
        name_en="Potato Tahdig",
        recognition_hints=(
            "round thin potato slices fried golden-brown as a rice-pot crust; not loose fries"
        ),
        kcal_per_100g=260,
        uncertainty_percent=27,
        default_portion_id="piece",
        portions=(
            PortionUnit("piece", "یک برش", 35),
            PortionUnit("three-pieces", "سه برش", 105),
        ),
    ),
    FoodProfile(
        id="salad-shirazi",
        name_fa="سالاد شیرازی",
        name_en="Salad Shirazi",
        recognition_hints=(
            "finely diced cucumber, tomato and onion salad, usually in a separate small pile "
            "or bowl without lettuce"
        ),
        kcal_per_100g=35,
        uncertainty_percent=22,
        default_portion_id="bowl",
        portions=(
            PortionUnit("tablespoon", "قاشق غذاخوری", 20),
            PortionUnit("bowl", "کاسه کوچک", 120),
        ),
    ),
    FoodProfile(
        id="plain-yogurt",
        name_fa="ماست ساده",
        name_en="Plain Yogurt",
        recognition_hints=(
            "smooth plain white yogurt served as a distinct side in a small bowl; "
            "no cucumber pieces or visible herbs"
        ),
        kcal_per_100g=65,
        uncertainty_percent=18,
        default_portion_id="bowl",
        portions=(
            PortionUnit("tablespoon", "قاشق غذاخوری", 25),
            PortionUnit("bowl", "کاسه کوچک", 150),
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
    FoodProfile(
        id="baghali-polo-goosht",
        name_fa="باقالی‌پلو با گوشت",
        name_en="Baghali Polo ba Goosht",
        recognition_hints=(
            "dill and broad-bean rice served with a distinct large braised lamb shank "
            "or chunk of red meat; not fish or chicken"
        ),
        kcal_per_100g=205,
        uncertainty_percent=27,
        default_portion_id="plate",
        portions=(
            PortionUnit("half-plate", "نصف بشقاب", 275),
            PortionUnit("plate", "بشقاب متوسط", 550),
        ),
    ),
    FoodProfile(
        id="kabab-bakhtiari",
        name_fa="کباب بختیاری",
        name_en="Kabab Bakhtiari",
        recognition_hints=(
            "alternating chunks of saffron chicken and red meat on the same skewer; "
            "not all-chicken Joojeh or flat Barg"
        ),
        kcal_per_100g=215,
        uncertainty_percent=20,
        default_portion_id="skewer",
        portions=(
            PortionUnit("half-skewer", "نصف سیخ", 75),
            PortionUnit("skewer", "یک سیخ", 150),
        ),
    ),
    FoodProfile(
        id="shishlik",
        name_fa="شیشلیک",
        name_en="Shishlik",
        recognition_hints=(
            "large grilled lamb rib chops with visible curved rib bones, usually several pieces"
        ),
        kcal_per_100g=265,
        uncertainty_percent=22,
        default_portion_id="piece",
        portions=(
            PortionUnit("piece", "یک تکه", 90),
            PortionUnit("serving", "یک پرس", 360),
        ),
    ),
    FoodProfile(
        id="kabab-tabei",
        name_fa="کباب تابه‌ای",
        name_en="Kabab Tabei",
        recognition_hints=(
            "pan-fried minced-meat strips or a flat meat layer with cooked tomato, "
            "served without skewers or grill marks"
        ),
        kcal_per_100g=240,
        uncertainty_percent=22,
        default_portion_id="piece",
        portions=(
            PortionUnit("half-piece", "نصف تکه", 75),
            PortionUnit("piece", "یک تکه", 150),
        ),
    ),
    FoodProfile(
        id="kabab-torsh",
        name_fa="کباب ترش",
        name_en="Kabab Torsh",
        recognition_hints=(
            "dark marinated grilled beef chunks coated with pomegranate and walnut-herb sauce; "
            "not plain red-meat kebab"
        ),
        kcal_per_100g=235,
        uncertainty_percent=23,
        default_portion_id="skewer",
        portions=(
            PortionUnit("half-skewer", "نصف سیخ", 70),
            PortionUnit("skewer", "یک سیخ", 140),
        ),
    ),
    FoodProfile(
        id="khoresh-bademjan",
        name_fa="خورش بادمجان",
        name_en="Khoresh Bademjan",
        recognition_hints=(
            "tomato-red meat stew with prominent whole fried eggplants and often tomato; "
            "no yellow split peas unlike Gheimeh Bademjan"
        ),
        kcal_per_100g=165,
        uncertainty_percent=24,
        default_portion_id="ladle",
        portions=(
            PortionUnit("tablespoon", "قاشق غذاخوری", 25),
            PortionUnit("ladle", "ملاقه", 180),
            PortionUnit("bowl", "کاسه متوسط", 360),
        ),
    ),
    FoodProfile(
        id="khoresh-bamieh",
        name_fa="خورش بامیه",
        name_en="Khoresh Bamieh",
        recognition_hints=(
            "red tomato-based meat stew with many clearly visible whole green okra pods; "
            "no eggplant, split peas or potato sticks"
        ),
        kcal_per_100g=125,
        uncertainty_percent=24,
        default_portion_id="ladle",
        portions=(
            PortionUnit("tablespoon", "قاشق غذاخوری", 25),
            PortionUnit("ladle", "ملاقه", 180),
            PortionUnit("bowl", "کاسه متوسط", 360),
        ),
    ),
    FoodProfile(
        id="khoresh-aloo-esfenaj",
        name_fa="خورش آلو اسفناج",
        name_en="Khoresh Aloo Esfenaj",
        recognition_hints=(
            "very dark spinach and herb stew with clearly visible whole dried plums and meat; "
            "no beans or celery stalks"
        ),
        kcal_per_100g=155,
        uncertainty_percent=24,
        default_portion_id="ladle",
        portions=(
            PortionUnit("tablespoon", "قاشق غذاخوری", 25),
            PortionUnit("ladle", "ملاقه", 180),
            PortionUnit("bowl", "کاسه متوسط", 360),
        ),
    ),
    FoodProfile(
        id="estamboli-polo",
        name_fa="استانبولی‌پلو",
        name_en="Estamboli Polo",
        recognition_hints=(
            "orange-red tomato rice with small potato cubes, usually without chopped green beans"
        ),
        kcal_per_100g=155,
        uncertainty_percent=20,
        default_portion_id="plate",
        portions=(
            PortionUnit("scoop", "کفگیر", 110),
            PortionUnit("plate", "بشقاب متوسط", 330),
        ),
    ),
    FoodProfile(
        id="reshteh-polo",
        name_fa="رشته‌پلو",
        name_en="Reshteh Polo",
        recognition_hints=(
            "rice visibly mixed with short browned toasted noodles, often topped with dates, "
            "raisins or minced meat"
        ),
        kcal_per_100g=185,
        uncertainty_percent=23,
        default_portion_id="plate",
        portions=(
            PortionUnit("scoop", "کفگیر", 110),
            PortionUnit("plate", "بشقاب متوسط", 330),
        ),
    ),
    FoodProfile(
        id="albaloo-polo",
        name_fa="آلبالوپلو",
        name_en="Albaloo Polo",
        recognition_hints=(
            "white or saffron rice densely dotted with red sour cherries, sometimes with "
            "small meatballs; cherries are larger and juicier than barberries"
        ),
        kcal_per_100g=185,
        uncertainty_percent=23,
        default_portion_id="plate",
        portions=(
            PortionUnit("scoop", "کفگیر", 110),
            PortionUnit("plate", "بشقاب متوسط", 330),
        ),
    ),
    FoodProfile(
        id="kalam-polo-shirazi",
        name_fa="کلم‌پلو شیرازی",
        name_en="Kalam Polo Shirazi",
        recognition_hints=(
            "green herb rice mixed with thin cabbage strips and usually served with small "
            "round meatballs; not dill rice"
        ),
        kcal_per_100g=175,
        uncertainty_percent=23,
        default_portion_id="plate",
        portions=(
            PortionUnit("scoop", "کفگیر", 110),
            PortionUnit("plate", "بشقاب متوسط", 330),
        ),
    ),
    FoodProfile(
        id="torsh-tareh",
        name_fa="ترش‌تره",
        name_en="Torsh Tareh",
        recognition_hints=(
            "thick bright-to-dark green Gilaki herb stew with garlic and egg, often showing "
            "set egg patches; no broad beans"
        ),
        kcal_per_100g=105,
        uncertainty_percent=25,
        default_portion_id="ladle",
        portions=(
            PortionUnit("tablespoon", "قاشق غذاخوری", 25),
            PortionUnit("ladle", "ملاقه", 180),
            PortionUnit("bowl", "کاسه متوسط", 360),
        ),
    ),
    FoodProfile(
        id="morgh-torsh",
        name_fa="مرغ ترش",
        name_en="Morgh Torsh",
        recognition_hints=(
            "distinct chicken pieces in a dark green northern Iranian herb, walnut and sour "
            "pomegranate sauce; chicken remains clearly visible"
        ),
        kcal_per_100g=190,
        uncertainty_percent=25,
        default_portion_id="piece",
        portions=(
            PortionUnit("half-piece", "نصف تکه مرغ", 100),
            PortionUnit("piece", "یک تکه مرغ با سس", 200),
        ),
    ),
    FoodProfile(
        id="vavishka",
        name_fa="واویشکا",
        name_en="Vavishka",
        recognition_hints=(
            "loose sauteed minced meat or chopped offal with onion and tomato, often topped "
            "with an egg; not shaped into patties"
        ),
        kcal_per_100g=210,
        uncertainty_percent=27,
        default_portion_id="plate",
        portions=(
            PortionUnit("tablespoon", "قاشق غذاخوری", 25),
            PortionUnit("plate", "بشقاب کوچک", 250),
        ),
    ),
    FoodProfile(
        id="mahi-shekam-por",
        name_fa="ماهی شکم‌پر",
        name_en="Mahi Shekam Por",
        recognition_hints=(
            "whole baked or fried fish split and visibly stuffed with dark herbs, walnuts "
            "and pomegranate mixture"
        ),
        kcal_per_100g=200,
        uncertainty_percent=27,
        default_portion_id="serving",
        portions=(
            PortionUnit("half-serving", "نصف پرس", 175),
            PortionUnit("serving", "یک پرس", 350),
        ),
    ),
    FoodProfile(
        id="ghalieh-mahi",
        name_fa="قلیه ماهی",
        name_en="Ghalieh Mahi",
        recognition_hints=(
            "very dark green-brown southern herb and tamarind stew with visible fish chunks; "
            "no kidney beans, celery or dried plums"
        ),
        kcal_per_100g=140,
        uncertainty_percent=25,
        default_portion_id="ladle",
        portions=(
            PortionUnit("tablespoon", "قاشق غذاخوری", 25),
            PortionUnit("ladle", "ملاقه", 180),
            PortionUnit("bowl", "کاسه متوسط", 360),
        ),
    ),
    FoodProfile(
        id="meygoo-polo",
        name_fa="میگوپلو",
        name_en="Meygoo Polo",
        recognition_hints=(
            "spiced yellow, orange or herb rice with multiple clearly visible curled shrimp"
        ),
        kcal_per_100g=180,
        uncertainty_percent=23,
        default_portion_id="plate",
        portions=(
            PortionUnit("scoop", "کفگیر", 110),
            PortionUnit("plate", "بشقاب متوسط", 350),
        ),
    ),
    FoodProfile(
        id="ash-doogh",
        name_fa="آش دوغ",
        name_en="Ash Doogh",
        recognition_hints=(
            "pale white yogurt-based soup densely flecked with green herbs and chickpeas, "
            "without noodles or dark kashk topping"
        ),
        kcal_per_100g=75,
        uncertainty_percent=22,
        default_portion_id="bowl",
        portions=(
            PortionUnit("ladle", "ملاقه", 180),
            PortionUnit("bowl", "کاسه متوسط", 400),
        ),
    ),
    FoodProfile(
        id="adasi",
        name_fa="عدسی",
        name_en="Adasi",
        recognition_hints=(
            "thick brown lentil soup or porridge with visible whole lentils; no rice grains "
            "and no long noodles"
        ),
        kcal_per_100g=105,
        uncertainty_percent=18,
        default_portion_id="bowl",
        portions=(
            PortionUnit("ladle", "ملاقه", 180),
            PortionUnit("bowl", "کاسه متوسط", 350),
        ),
    ),
    FoodProfile(
        id="halim",
        name_fa="حلیم",
        name_en="Halim",
        recognition_hints=(
            "smooth beige elastic wheat-and-meat porridge, commonly topped with cinnamon, "
            "sugar and melted butter; no visible lentils"
        ),
        kcal_per_100g=145,
        uncertainty_percent=24,
        default_portion_id="bowl",
        portions=(
            PortionUnit("tablespoon", "قاشق غذاخوری", 25),
            PortionUnit("bowl", "کاسه متوسط", 350),
        ),
    ),
    FoodProfile(
        id="margherita-pizza",
        name_fa="پیتزا مارگاریتا",
        name_en="Margherita Pizza",
        recognition_hints=(
            "round pizza with red tomato sauce, melted white cheese and sparse basil; "
            "no pepperoni or heavy meat topping"
        ),
        kcal_per_100g=260,
        uncertainty_percent=24,
        default_portion_id="slice",
        portions=(
            PortionUnit("slice", "یک برش", 110),
            PortionUnit("small-pizza", "یک پیتزای کوچک", 440),
        ),
    ),
    FoodProfile(
        id="pepperoni-pizza",
        name_fa="پیتزا پپرونی",
        name_en="Pepperoni Pizza",
        recognition_hints=(
            "cheese pizza covered with multiple small round red pepperoni slices"
        ),
        kcal_per_100g=295,
        uncertainty_percent=24,
        default_portion_id="slice",
        portions=(
            PortionUnit("slice", "یک برش", 115),
            PortionUnit("small-pizza", "یک پیتزای کوچک", 460),
        ),
    ),
    FoodProfile(
        id="hamburger",
        name_fa="همبرگر",
        name_en="Hamburger",
        recognition_hints=(
            "round bun sandwich with one grilled beef patty and vegetables, without a "
            "visible cheese slice"
        ),
        kcal_per_100g=250,
        uncertainty_percent=25,
        default_portion_id="item",
        portions=(
            PortionUnit("half-item", "نصف عدد", 110),
            PortionUnit("item", "یک عدد", 220),
        ),
    ),
    FoodProfile(
        id="cheeseburger",
        name_fa="چیزبرگر",
        name_en="Cheeseburger",
        recognition_hints=(
            "round bun sandwich with a beef patty and a clearly visible melted yellow cheese slice"
        ),
        kcal_per_100g=285,
        uncertainty_percent=25,
        default_portion_id="item",
        portions=(
            PortionUnit("half-item", "نصف عدد", 115),
            PortionUnit("item", "یک عدد", 230),
        ),
    ),
    FoodProfile(
        id="hot-dog",
        name_fa="هات‌داگ",
        name_en="Hot Dog",
        recognition_hints=(
            "long sausage inside a split elongated bun, commonly topped with sauces"
        ),
        kcal_per_100g=290,
        uncertainty_percent=26,
        default_portion_id="item",
        portions=(
            PortionUnit("half-item", "نصف عدد", 85),
            PortionUnit("item", "یک عدد", 170),
        ),
    ),
    FoodProfile(
        id="french-fries",
        name_fa="سیب‌زمینی سرخ‌شده",
        name_en="French Fries",
        recognition_hints=(
            "pile of thin golden fried potato sticks; not round potato tahdig slices"
        ),
        kcal_per_100g=312,
        uncertainty_percent=20,
        default_portion_id="serving",
        portions=(
            PortionUnit("small-serving", "پرس کوچک", 80),
            PortionUnit("serving", "پرس متوسط", 150),
        ),
    ),
    FoodProfile(
        id="fried-chicken",
        name_fa="مرغ سوخاری",
        name_en="Fried Chicken",
        recognition_hints=(
            "chicken pieces covered in a thick rough golden-brown crispy breadcrumb coating"
        ),
        kcal_per_100g=275,
        uncertainty_percent=25,
        default_portion_id="piece",
        portions=(
            PortionUnit("piece", "یک تکه", 120),
            PortionUnit("three-pieces", "سه تکه", 360),
        ),
    ),
    FoodProfile(
        id="falafel-sandwich",
        name_fa="ساندویچ فلافل",
        name_en="Falafel Sandwich",
        recognition_hints=(
            "flatbread or baguette sandwich filled with several round brown falafel balls, "
            "pickles and vegetables"
        ),
        kcal_per_100g=260,
        uncertainty_percent=27,
        default_portion_id="item",
        portions=(
            PortionUnit("half-item", "نصف ساندویچ", 125),
            PortionUnit("item", "یک ساندویچ", 250),
        ),
    ),
    FoodProfile(
        id="chicken-sandwich",
        name_fa="ساندویچ مرغ",
        name_en="Chicken Sandwich",
        recognition_hints=(
            "bread roll or sliced bread filled mainly with visible chicken pieces and vegetables; "
            "not a breaded fried chicken burger"
        ),
        kcal_per_100g=220,
        uncertainty_percent=27,
        default_portion_id="item",
        portions=(
            PortionUnit("half-item", "نصف ساندویچ", 120),
            PortionUnit("item", "یک ساندویچ", 240),
        ),
    ),
    FoodProfile(
        id="olivieh-sandwich",
        name_fa="ساندویچ الویه",
        name_en="Olivieh Sandwich",
        recognition_hints=(
            "bread filled with pale creamy potato, chicken, egg and mayonnaise salad, "
            "often with pickles"
        ),
        kcal_per_100g=250,
        uncertainty_percent=27,
        default_portion_id="item",
        portions=(
            PortionUnit("half-item", "نصف ساندویچ", 125),
            PortionUnit("item", "یک ساندویچ", 250),
        ),
    ),
    FoodProfile(
        id="bandari-sandwich",
        name_fa="ساندویچ بندری",
        name_en="Bandari Sandwich",
        recognition_hints=(
            "baguette filled with reddish spicy sliced sausage, onion and tomato sauce"
        ),
        kcal_per_100g=285,
        uncertainty_percent=27,
        default_portion_id="item",
        portions=(
            PortionUnit("half-item", "نصف ساندویچ", 130),
            PortionUnit("item", "یک ساندویچ", 260),
        ),
    ),
    FoodProfile(
        id="tuna-sandwich",
        name_fa="ساندویچ تن ماهی",
        name_en="Tuna Sandwich",
        recognition_hints=(
            "bread filled with flaky pale tuna, often mixed with mayonnaise and vegetables; "
            "no whole chicken pieces"
        ),
        kcal_per_100g=230,
        uncertainty_percent=26,
        default_portion_id="item",
        portions=(
            PortionUnit("half-item", "نصف ساندویچ", 115),
            PortionUnit("item", "یک ساندویچ", 230),
        ),
    ),
    FoodProfile(
        id="apple",
        name_fa="سیب",
        name_en="Apple",
        recognition_hints="whole or sliced round red, green or yellow apple with firm pale flesh",
        kcal_per_100g=52,
        uncertainty_percent=10,
        default_portion_id="item",
        portions=(
            PortionUnit("small-item", "یک عدد کوچک", 120),
            PortionUnit("item", "یک عدد متوسط", 180),
        ),
    ),
    FoodProfile(
        id="banana",
        name_fa="موز",
        name_en="Banana",
        recognition_hints="curved yellow banana, whole or peeled into pale cream fruit",
        kcal_per_100g=89,
        uncertainty_percent=10,
        default_portion_id="item",
        portions=(
            PortionUnit("small-item", "یک عدد کوچک", 80),
            PortionUnit("item", "یک عدد متوسط", 120),
        ),
    ),
    FoodProfile(
        id="orange",
        name_fa="پرتقال",
        name_en="Orange",
        recognition_hints="round orange-colored citrus fruit with thick peel or segmented orange flesh",
        kcal_per_100g=47,
        uncertainty_percent=10,
        default_portion_id="item",
        portions=(
            PortionUnit("small-item", "یک عدد کوچک", 130),
            PortionUnit("item", "یک عدد متوسط", 180),
        ),
    ),
    FoodProfile(
        id="tangerine",
        name_fa="نارنگی",
        name_en="Tangerine",
        recognition_hints=(
            "small slightly flattened orange citrus fruit with loose peel and small segments"
        ),
        kcal_per_100g=53,
        uncertainty_percent=10,
        default_portion_id="item",
        portions=(
            PortionUnit("item", "یک عدد", 100),
            PortionUnit("two-items", "دو عدد", 200),
        ),
    ),
    FoodProfile(
        id="grapes",
        name_fa="انگور",
        name_en="Grapes",
        recognition_hints="cluster or pile of many small round green, red or dark grapes",
        kcal_per_100g=69,
        uncertainty_percent=12,
        default_portion_id="cup",
        portions=(
            PortionUnit("small-bunch", "خوشه کوچک", 100),
            PortionUnit("cup", "یک لیوان", 150),
        ),
    ),
    FoodProfile(
        id="watermelon",
        name_fa="هندوانه",
        name_en="Watermelon",
        recognition_hints=(
            "large wedge or cubes of bright red watery fruit with green rind and possible black seeds"
        ),
        kcal_per_100g=30,
        uncertainty_percent=10,
        default_portion_id="slice",
        portions=(
            PortionUnit("slice", "یک برش", 300),
            PortionUnit("bowl", "یک کاسه خردشده", 250),
        ),
    ),
    FoodProfile(
        id="melon",
        name_fa="خربزه یا طالبی",
        name_en="Melon",
        recognition_hints=(
            "pale yellow, cream or orange melon wedges or cubes with a firm rind; not red watermelon"
        ),
        kcal_per_100g=35,
        uncertainty_percent=12,
        default_portion_id="slice",
        portions=(
            PortionUnit("slice", "یک برش", 200),
            PortionUnit("bowl", "یک کاسه خردشده", 250),
        ),
    ),
    FoodProfile(
        id="dates",
        name_fa="خرما",
        name_en="Dates",
        recognition_hints="small oval glossy brown dried dates, with or without visible pits",
        kcal_per_100g=282,
        uncertainty_percent=12,
        default_portion_id="three-items",
        portions=(
            PortionUnit("item", "یک عدد", 8),
            PortionUnit("three-items", "سه عدد", 24),
        ),
    ),
    FoodProfile(
        id="plain-cake",
        name_fa="کیک ساده",
        name_en="Plain Cake",
        recognition_hints=(
            "slice of soft baked sponge cake without cream layers or thick frosting"
        ),
        kcal_per_100g=360,
        uncertainty_percent=25,
        default_portion_id="slice",
        portions=(
            PortionUnit("small-slice", "برش کوچک", 45),
            PortionUnit("slice", "یک برش", 80),
        ),
    ),
    FoodProfile(
        id="dry-pastry",
        name_fa="شیرینی خشک",
        name_en="Dry Pastry",
        recognition_hints=(
            "small dry baked cookie-like Iranian pastry without whipped cream filling"
        ),
        kcal_per_100g=450,
        uncertainty_percent=28,
        default_portion_id="piece",
        portions=(
            PortionUnit("piece", "یک عدد", 25),
            PortionUnit("three-pieces", "سه عدد", 75),
        ),
    ),
    FoodProfile(
        id="cream-pastry",
        name_fa="شیرینی تر یا خامه‌ای",
        name_en="Cream Pastry",
        recognition_hints=(
            "individual soft pastry or cake visibly layered or filled with whipped cream"
        ),
        kcal_per_100g=350,
        uncertainty_percent=28,
        default_portion_id="piece",
        portions=(
            PortionUnit("small-piece", "یک عدد کوچک", 50),
            PortionUnit("piece", "یک عدد", 90),
        ),
    ),
    FoodProfile(
        id="biscuit",
        name_fa="بیسکویت",
        name_en="Biscuit",
        recognition_hints="small flat crisp baked biscuit, plain or lightly patterned",
        kcal_per_100g=440,
        uncertainty_percent=22,
        default_portion_id="three-pieces",
        portions=(
            PortionUnit("piece", "یک عدد", 12),
            PortionUnit("three-pieces", "سه عدد", 36),
        ),
    ),
    FoodProfile(
        id="chocolate",
        name_fa="شکلات",
        name_en="Chocolate",
        recognition_hints="solid brown chocolate squares, bar pieces or individually wrapped chocolate",
        kcal_per_100g=535,
        uncertainty_percent=20,
        default_portion_id="piece",
        portions=(
            PortionUnit("square", "یک مربع", 10),
            PortionUnit("piece", "یک بسته کوچک", 30),
        ),
    ),
    FoodProfile(
        id="potato-chips",
        name_fa="چیپس سیب‌زمینی",
        name_en="Potato Chips",
        recognition_hints=(
            "pile of very thin curved crisp fried potato slices; not thick French fries"
        ),
        kcal_per_100g=536,
        uncertainty_percent=18,
        default_portion_id="small-bag",
        portions=(
            PortionUnit("handful", "یک مشت", 30),
            PortionUnit("small-bag", "بسته کوچک", 60),
        ),
    ),
    FoodProfile(
        id="pistachios",
        name_fa="پسته",
        name_en="Pistachios",
        recognition_hints=(
            "small beige split shells revealing green pistachio kernels, or loose green kernels"
        ),
        kcal_per_100g=560,
        uncertainty_percent=15,
        default_portion_id="handful",
        portions=(
            PortionUnit("tablespoon", "قاشق غذاخوری مغز", 12),
            PortionUnit("handful", "یک مشت", 30),
        ),
    ),
    FoodProfile(
        id="mixed-nuts",
        name_fa="آجیل مخلوط",
        name_en="Mixed Nuts",
        recognition_hints=(
            "mixed bowl or handful containing visibly different nuts such as pistachios, "
            "almonds, cashews and walnuts"
        ),
        kcal_per_100g=600,
        uncertainty_percent=20,
        default_portion_id="handful",
        portions=(
            PortionUnit("tablespoon", "قاشق غذاخوری", 15),
            PortionUnit("handful", "یک مشت", 30),
        ),
    ),
    FoodProfile(
        id="milk",
        name_fa="شیر",
        name_en="Milk",
        recognition_hints=(
            "plain opaque white milk in a glass or cup; no visible yogurt thickness or foam art"
        ),
        kcal_per_100g=61,
        uncertainty_percent=18,
        default_portion_id="glass",
        portions=(
            PortionUnit("small-glass", "لیوان کوچک", 150),
            PortionUnit("glass", "یک لیوان", 240),
        ),
    ),
    FoodProfile(
        id="doogh",
        name_fa="دوغ",
        name_en="Doogh",
        recognition_hints=(
            "thin white yogurt drink in a glass, sometimes with mint flecks or light foam"
        ),
        kcal_per_100g=30,
        uncertainty_percent=20,
        default_portion_id="glass",
        portions=(
            PortionUnit("small-glass", "لیوان کوچک", 150),
            PortionUnit("glass", "یک لیوان", 250),
        ),
    ),
    FoodProfile(
        id="cola",
        name_fa="نوشابه کولا",
        name_en="Cola Soft Drink",
        recognition_hints=(
            "dark brown carbonated soft drink in a glass, can or labeled bottle; when the "
            "sugar-free label is not readable, do not infer diet or zero from liquid color"
        ),
        kcal_per_100g=42,
        uncertainty_percent=12,
        default_portion_id="can",
        portions=(
            PortionUnit("glass", "یک لیوان", 250),
            PortionUnit("can", "یک قوطی", 330),
            PortionUnit("small-bottle", "بطری کوچک", 500),
        ),
    ),
    FoodProfile(
        id="diet-cola",
        name_fa="نوشابه کولا بدون قند",
        name_en="Diet or Zero Cola",
        recognition_hints=(
            "cola whose container visibly and clearly says diet, zero or sugar-free; "
            "never identify from the dark liquid alone"
        ),
        kcal_per_100g=1,
        uncertainty_percent=50,
        default_portion_id="can",
        portions=(
            PortionUnit("glass", "یک لیوان", 250),
            PortionUnit("can", "یک قوطی", 330),
            PortionUnit("small-bottle", "بطری کوچک", 500),
        ),
    ),
    FoodProfile(
        id="orange-soda",
        name_fa="نوشابه پرتقالی",
        name_en="Orange Soda",
        recognition_hints=(
            "bright orange carbonated soft drink in a glass or orange-flavored labeled container"
        ),
        kcal_per_100g=45,
        uncertainty_percent=15,
        default_portion_id="can",
        portions=(
            PortionUnit("glass", "یک لیوان", 250),
            PortionUnit("can", "یک قوطی", 330),
            PortionUnit("small-bottle", "بطری کوچک", 500),
        ),
    ),
    FoodProfile(
        id="malt-beverage",
        name_fa="دلستر یا ماءالشعیر",
        name_en="Non-Alcoholic Malt Beverage",
        recognition_hints=(
            "golden or amber fizzy malt beverage with a foamy head, commonly in a labeled "
            "non-alcoholic malt bottle or can"
        ),
        kcal_per_100g=45,
        uncertainty_percent=22,
        default_portion_id="bottle",
        portions=(
            PortionUnit("glass", "یک لیوان", 250),
            PortionUnit("can", "یک قوطی", 330),
            PortionUnit("bottle", "یک بطری", 330),
        ),
    ),
    FoodProfile(
        id="lemonade",
        name_fa="لیموناد",
        name_en="Lemonade",
        recognition_hints=(
            "pale yellow or cloudy lemon drink, often served with lemon slices, ice or mint; "
            "not orange soda"
        ),
        kcal_per_100g=40,
        uncertainty_percent=25,
        default_portion_id="glass",
        portions=(
            PortionUnit("glass", "یک لیوان", 250),
            PortionUnit("bottle", "یک بطری کوچک", 330),
        ),
    ),
)


RECOGNITION_FAMILIES: dict[str, tuple[str, ...]] = {
    "stews": (
        "ghormeh-sabzi",
        "fesenjan",
        "baghala-ghatogh",
        "anarbij",
        "gheimeh",
        "gheimeh-bademjan",
        "khoresh-karafs",
        "khoresh-bademjan",
        "khoresh-bamieh",
        "khoresh-aloo-esfenaj",
        "torsh-tareh",
        "morgh-torsh",
        "ghalieh-mahi",
    ),
    "rice dishes": (
        "cooked-rice",
        "saffron-rice",
        "rice-tahdig",
        "bread-tahdig",
        "potato-tahdig",
        "zereshk-polo-morgh",
        "loobia-polo",
        "adas-polo",
        "sabzi-polo-mahi",
        "tahchin-morgh",
        "baghali-polo-goosht",
        "estamboli-polo",
        "reshteh-polo",
        "albaloo-polo",
        "kalam-polo-shirazi",
        "meygoo-polo",
    ),
    "kebabs": (
        "koobideh-kebab",
        "joojeh-kebab",
        "kabab-barg",
        "kabab-bakhtiari",
        "shishlik",
        "kabab-tabei",
        "kabab-torsh",
    ),
    "soups and porridges": (
        "ash-reshteh",
        "abgoosht",
        "ash-doogh",
        "adasi",
        "halim",
    ),
    "egg and vegetable dishes": (
        "kashk-bademjan",
        "mirza-ghasemi",
        "kookoo-sabzi",
        "kotlet",
        "dolmeh-barg-mo",
    ),
    "regional mains": (
        "koofteh-tabrizi",
        "vavishka",
        "mahi-shekam-por",
    ),
    "side dishes": (
        "salad-shirazi",
        "plain-yogurt",
    ),
    "fast food": (
        "margherita-pizza",
        "pepperoni-pizza",
        "hamburger",
        "cheeseburger",
        "hot-dog",
        "french-fries",
        "fried-chicken",
    ),
    "sandwiches": (
        "falafel-sandwich",
        "chicken-sandwich",
        "olivieh-sandwich",
        "bandari-sandwich",
        "tuna-sandwich",
    ),
    "fruits": (
        "apple",
        "banana",
        "orange",
        "tangerine",
        "grapes",
        "watermelon",
        "melon",
        "dates",
    ),
    "snacks and sweets": (
        "plain-cake",
        "dry-pastry",
        "cream-pastry",
        "biscuit",
        "chocolate",
        "potato-chips",
    ),
    "nuts": (
        "pistachios",
        "mixed-nuts",
    ),
    "drinks and dairy": (
        "milk",
        "doogh",
        "cola",
        "diet-cola",
        "orange-soda",
        "malt-beverage",
        "lemonade",
    ),
    "pasta": ("iranian-macaroni",),
}


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
