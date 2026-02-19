#!/usr/bin/env python3
"""
Generates structured appearance data for characters in character_enrichment.json.
Infers physical descriptions from cultural origin, title, personality, role, and birth date.

Usage:
    python3 tools/build_appearances.py                # Preview (dry run)
    python3 tools/build_appearances.py --write        # Write to character_enrichment.json
"""

import json
import sys
import re
from pathlib import Path

ENRICHMENT_PATH = Path(__file__).parent.parent / "resources" / "data" / "character_enrichment.json"
REFERENCE_YEAR = 1439  # Current campaign year

# ─── Cultural / Ethnic Rules ───

CULTURE_RULES = {
    "castilian": {
        "skin": "olive Castilian complexion",
        "hair_colors": ["dark brown", "black", "dark"],
        "eye_colors": ["dark brown", "brown", "hazel"],
        "art_style": "medieval oil portrait, warm candlelight, realistic detail, 15th century Castilian court",
    },
    "aragonese": {
        "skin": "olive Mediterranean complexion",
        "hair_colors": ["dark brown", "dark", "brown"],
        "eye_colors": ["dark brown", "brown", "hazel"],
        "art_style": "medieval oil portrait, warm light, realistic detail, 15th century Aragonese court",
    },
    "catalan": {
        "skin": "olive Mediterranean complexion",
        "hair_colors": ["dark brown", "dark", "brown"],
        "eye_colors": ["brown", "dark brown", "hazel"],
        "art_style": "medieval oil portrait, warm Mediterranean light, realistic detail, 15th century",
    },
    "portuguese": {
        "skin": "fair Iberian complexion",
        "hair_colors": ["dark brown", "brown", "dark"],
        "eye_colors": ["brown", "dark brown", "hazel"],
        "art_style": "medieval oil portrait, warm light, realistic detail, 15th century Portuguese court",
    },
    "italian": {
        "skin": "fair Italian complexion",
        "hair_colors": ["dark", "dark brown", "brown"],
        "eye_colors": ["dark brown", "brown", "hazel"],
        "art_style": "medieval oil portrait, warm light, realistic detail, Italian Renaissance influence",
    },
    "florentine": {
        "skin": "fair Tuscan complexion",
        "hair_colors": ["dark brown", "auburn", "brown"],
        "eye_colors": ["brown", "hazel", "dark"],
        "art_style": "Renaissance oil portrait, warm Florentine light, realistic detail, 15th century",
    },
    "venetian": {
        "skin": "fair Venetian complexion",
        "hair_colors": ["dark brown", "dark", "brown"],
        "eye_colors": ["dark", "brown", "grey"],
        "art_style": "medieval oil portrait, soft Venetian light, realistic detail, 15th century",
    },
    "genoese": {
        "skin": "olive Ligurian complexion",
        "hair_colors": ["dark", "dark brown", "black"],
        "eye_colors": ["dark brown", "brown", "dark"],
        "art_style": "medieval oil portrait, Mediterranean light, realistic detail, 15th century Genoa",
    },
    "ferrarese": {
        "skin": "fair northern Italian complexion",
        "hair_colors": ["dark", "dark brown", "brown"],
        "eye_colors": ["dark", "brown", "grey-green"],
        "art_style": "medieval oil portrait, warm light, realistic detail, Italian Renaissance",
    },
    "french": {
        "skin": "fair complexion",
        "hair_colors": ["brown", "dark brown", "light brown"],
        "eye_colors": ["blue", "grey", "brown"],
        "art_style": "medieval oil portrait, soft light, realistic detail, 15th century French style",
    },
    "polish": {
        "skin": "fair Slavic complexion",
        "hair_colors": ["light brown", "brown", "dark blond"],
        "eye_colors": ["blue", "grey", "light brown"],
        "art_style": "medieval oil portrait, cool northern light, realistic detail, 15th century Polish court",
    },
    "hungarian": {
        "skin": "fair Central European complexion",
        "hair_colors": ["dark brown", "brown", "dark"],
        "eye_colors": ["brown", "hazel", "grey"],
        "art_style": "medieval oil portrait, warm light, realistic detail, 15th century Hungarian court",
    },
    "ottoman": {
        "skin": "warm olive complexion",
        "hair_colors": ["black", "dark"],
        "eye_colors": ["dark brown", "black", "dark"],
        "art_style": "medieval portrait, warm light, realistic detail, Ottoman imperial style",
    },
    "byzantine": {
        "skin": "olive Greek complexion",
        "hair_colors": ["dark brown", "dark", "black"],
        "eye_colors": ["dark brown", "brown", "dark"],
        "art_style": "medieval portrait, golden Byzantine light, realistic detail, 15th century Constantinople",
    },
    "english": {
        "skin": "fair English complexion",
        "hair_colors": ["brown", "light brown", "sandy"],
        "eye_colors": ["blue", "grey", "hazel"],
        "art_style": "medieval oil portrait, cool light, realistic detail, 15th century English style",
    },
    "german": {
        "skin": "fair Germanic complexion",
        "hair_colors": ["brown", "light brown", "blond"],
        "eye_colors": ["blue", "grey", "light brown"],
        "art_style": "medieval oil portrait, cool light, realistic detail, 15th century Germanic style",
    },
    "sephardic": {
        "skin": "olive Sephardic complexion",
        "hair_colors": ["dark", "dark brown", "black"],
        "eye_colors": ["dark brown", "brown", "dark"],
        "art_style": "medieval oil portrait, warm light, realistic detail, 15th century Iberian",
    },
    "malian": {
        "skin": "dark West African complexion",
        "hair_colors": ["black, tightly curled"],
        "eye_colors": ["dark brown", "black"],
        "art_style": "medieval portrait, warm light, realistic detail, West African court style",
    },
    "sicilian": {
        "skin": "sun-darkened Mediterranean complexion",
        "hair_colors": ["dark", "black", "dark brown"],
        "eye_colors": ["dark brown", "brown", "dark"],
        "art_style": "medieval oil portrait, warm Mediterranean light, realistic detail, 15th century",
    },
}

# ─── Role-Based Clothing Rules ───

def get_clothing_for_role(title, personality, culture):
    """Returns (default_clothing, court_clothing, battle_clothing) based on role."""
    title_lower = title.lower() if title else ""
    personality_str = " ".join(personality).lower() if personality else ""

    # Royal family
    if any(w in title_lower for w in ["king", "queen", "prince", "princess", "sultan", "emperor", "empress", "despot"]):
        if "deceased" in title_lower:
            return ("", "", "")
        if "sultan" in title_lower:
            return (
                "rich silk kaftan with gold embroidery, jeweled turban",
                "ceremonial Ottoman court robes, imperial turban with jeweled aigrette",
                "ornate Ottoman armor with gold inlay, plumed helmet",
            )
        if "emperor" in title_lower:
            return (
                "imperial purple robes with gold embroidery, Byzantine imperial diadem",
                "full imperial regalia, jeweled loros and chlamys",
                "",
            )
        if "queen" in title_lower or "princess" in title_lower:
            return (
                "rich silk gown with gold embroidery, jeweled circlet",
                "full court gown with ermine trim, royal diadem",
                "",
            )
        return (
            "rich doublet with royal arms, gold chain of office",
            "full royal robes with ermine-trimmed mantle, crown",
            "polished plate armor bearing royal arms",
        )

    # Pope
    if "pope" in title_lower:
        return (
            "white papal cassock, red papal shoes, pectoral cross",
            "full papal vestments, tiara, pallium",
            "",
        )

    # Cardinals
    if "cardinal" in title_lower:
        return (
            "scarlet cardinal's cassock with biretta, pectoral cross",
            "full cardinal's choir dress, cappa magna",
            "",
        )

    # Bishops / Archbishops
    if "bishop" in title_lower or "archbishop" in title_lower:
        return (
            "episcopal purple cassock, pectoral cross, biretta",
            "full episcopal vestments with mitre and crozier",
            "",
        )

    # Abbots
    if "abbot" in title_lower:
        return (
            "black monastic habit with abbatial cross",
            "full abbatial vestments",
            "",
        )

    # Friars / Brothers / Monks
    if any(w in title_lower for w in ["friar", "fray", "brother", "fra ", "master general"]):
        order = "brown"
        if "dominic" in title_lower or "dominic" in personality_str or "preacher" in title_lower:
            order = "white and black Dominican"
        elif "hieronymite" in personality_str:
            order = "brown Hieronymite"
        elif "francisc" in personality_str:
            order = "grey Franciscan"
        return (
            f"plain {order} habit, rope belt, wooden crucifix",
            f"same plain {order} habit, refuses court finery",
            "",
        )

    # Priests / Fathers
    if any(w in title_lower for w in ["priest", "father", "canon"]):
        return (
            "black cassock, white collar, simple crucifix",
            "black cassock with surplice",
            "",
        )

    # Patriarch (Orthodox)
    if "patriarch" in title_lower and "family" not in title_lower:
        return (
            "black Orthodox patriarchal robes, engolpion cross",
            "full patriarchal vestments, jeweled panagia, pastoral staff",
            "",
        )

    # Metropolitan / Orthodox clergy
    if "metropolitan" in title_lower:
        return (
            "black monastic habit with episcopal panagia",
            "full hierarchical vestments, mitre, pastoral staff",
            "",
        )

    # Orthodox theologian/scholar
    if "theologian" in title_lower or "scholar" in title_lower:
        return (
            "simple dark scholar's robe, ink-stained fingers",
            "dark academic robe with scholar's hood",
            "",
        )

    # Grand Master / Military Order
    if "grand master" in title_lower or "master of the order" in title_lower:
        return (
            "black surcoat with white Hospitaller cross, chain of office",
            "full ceremonial Order robes with grand master's insignia",
            "plate armor with Order's cross and grand master's cape",
        )

    # Military Order members
    if "order of calatrava" in title_lower:
        return (
            "white robe with red Calatrava cross",
            "ceremonial Calatrava Order robes",
            "armor with red cross of Calatrava",
        )

    # Admirals
    if "admiral" in title_lower:
        return (
            "naval officer's doublet, compass rose medallion",
            "formal admiral's robes with chain of naval office",
            "half-armor suited for shipboard combat",
        )

    # Constable
    if "constable" in title_lower:
        return (
            "dark velvet doublet with silver chain of the Constable",
            "black and silver robes of the Constable, chain of office",
            "well-worn plate armor, practical and unadorned",
        )

    # Military commanders / captains / commanders / sergeants / soldiers
    if any(w in title_lower for w in ["captain", "commander", "sergeant", "hetman"]) or "ban of" in title_lower:
        return (
            "practical military doublet with officer's insignia",
            "dress uniform with officer's chain",
            "well-used plate armor and command sash",
        )

    # Knights
    if any(w in title_lower for w in ["knight", "sir "]):
        return (
            "practical doublet with family arms, sword at hip",
            "fine doublet with heraldic surcoat",
            "full plate armor with heraldic surcoat and visored helm",
        )

    # Soldiers (named soldiers, lower rank)
    if any(w in title_lower for w in ["soldier", "officer"]):
        return (
            "leather jerkin over padded gambeson, simple sword",
            "",
            "mail hauberk with padded surcoat, kettle helm",
        )

    # Marquess / Count / Viscount / Duke / Nobleman / Adelantado
    if any(w in title_lower for w in ["marquess", "count", "viscount", "duke", "lord", "adelantado", "nobleman", "noble"]):
        return (
            "fine wool doublet with family arms, leather belt with sword",
            "rich velvet robes with family heraldry, gold chain",
            "polished plate armor with family crest",
        )

    # Noblewoman / Lady
    if any(w in title_lower for w in ["noblewoman", "lady"]):
        return (
            "fine silk gown with embroidered bodice",
            "rich velvet gown with family jewels and gold circlet",
            "",
        )

    # Governess
    if "governess" in title_lower:
        return (
            "dignified dark wool gown, keys at her belt",
            "modest but well-made court gown",
            "",
        )

    # Seamstress / Tailor / Craftsman
    if any(w in title_lower for w in ["seamstress", "tailor", "craftsman", "artisan", "blacksmith"]):
        return (
            "practical working clothes, leather apron, tools of trade",
            "",
            "",
        )

    # Banker / Merchant
    if any(w in title_lower for w in ["banker", "merchant", "principal of banco"]):
        return (
            "rich but understated dark wool doublet, money purse at belt",
            "fine dark silk robes, gold chain, rings",
            "",
        )

    # Mining engineer
    if any(w in title_lower for w in ["mining", "engineer"]):
        return (
            "sturdy working clothes, leather jerkin, dust-covered boots",
            "",
            "",
        )

    # Printer / Type specialist
    if any(w in title_lower for w in ["printer", "type-casting"]):
        return (
            "craftsman's working clothes, ink-stained leather apron",
            "",
            "",
        )

    # Doctor / Physician
    if any(w in title_lower for w in ["dr.", "physician"]):
        return (
            "dark scholar's robe with physician's satchel",
            "physician's formal dark robe",
            "",
        )

    # Spymaster
    if "spymaster" in title_lower:
        return (
            "plain dark merchant's clothes that blend into any crowd",
            "unassuming dark doublet, deliberately understated",
            "",
        )

    # Poison expert
    if "poison" in title_lower:
        return (
            "dark scholar's robe, leather gloves, glass vials in belt pouch",
            "modest dark robe, same leather gloves",
            "",
        )

    # Food taster
    if "food taster" in title_lower:
        return (
            "simple household servant's tunic, clean and practical",
            "",
            "",
        )

    # Ambassador
    if "ambassador" in title_lower:
        return (
            "rich robes in the style of their homeland, diplomatic insignia",
            "full ceremonial diplomatic robes",
            "",
        )

    # Harbor master / Port official
    if "harbor" in title_lower or "port" in title_lower:
        return (
            "practical maritime official's coat, ledger book in hand",
            "",
            "",
        )

    # Representative / civic leader
    if any(w in title_lower for w in ["representative", "patrician", "civic"]):
        return (
            "respectable merchant's wool doublet, civic medallion",
            "formal civic robes",
            "",
        )

    # Household servant
    if any(w in title_lower for w in ["servant", "attendant", "lady-in-waiting"]):
        return (
            "neat household livery in royal colours",
            "",
            "",
        )

    # Wall worker / common worker
    if "worker" in title_lower:
        return (
            "rough working tunic, calloused hands, sturdy boots",
            "",
            "",
        )

    # Citizen / commoner
    if "citizen" in title_lower:
        return (
            "simple but clean working clothes",
            "",
            "",
        )

    # Default: modest clothing
    return (
        "modest dark doublet, practical and well-worn",
        "",
        "",
    )


# ─── Gender Detection ───

FEMALE_INDICATORS = {
    "queen", "princess", "noblewoman", "lady", "governess", "seamstress",
    "wife", "donna", "doña", "beatriz", "lucia", "maria", "isabella",
    "alessandra", "giulia", "francesca", "caterina", "filipa", "leonor",
    "ines", "marta", "mencia", "anna", "eudokia", "beatrice",
}

MALE_INDICATORS = {
    "king", "prince", "duke", "count", "marquess", "viscount",
    "lord", "bishop", "cardinal", "pope", "friar", "fray", "brother",
    "father", "abbot", "captain", "commander", "sergeant", "admiral",
    "sultan", "emperor", "hetman", "ban", "knight", "sir", "despot",
    "master", "dr.", "don",
}

def detect_gender(char_id, title, name=""):
    """Detect gender from title and character ID."""
    combined = (char_id + " " + title + " " + name).lower()

    for indicator in FEMALE_INDICATORS:
        if indicator in combined:
            return "female"

    for indicator in MALE_INDICATORS:
        if indicator in combined:
            return "male"

    # Check ID patterns
    if char_id.endswith("a") and char_id not in ("musa_keita", "garcia", "daza"):
        # Many female names end in 'a' in Romance languages, but not all
        pass

    return "male"  # Default assumption for 15th century political/military figures


# ─── Culture Detection ───

def detect_culture(char_id, title, personality, location):
    """Detect cultural origin from character data."""
    combined = (char_id + " " + title + " " + " ".join(personality or []) + " " + (location or "")).lower()

    # Check personality and title first (higher priority than location)
    pers_title = (char_id + " " + title + " " + " ".join(personality or [])).lower()

    # Explicit ethnic/origin markers in personality/title take priority over location
    if any(w in pers_title for w in ["english", "england", "beaumont", "woodville"]):
        return "english"
    if any(w in pers_title for w in ["german", "saxon", "strasbourg", "steinberg", "wenzel", "moller"]):
        return "german"
    if any(w in pers_title for w in ["french", "breton", "france", "anjou", "rochetaillée", "aléman", "coetivy"]):
        return "french"
    if any(w in pers_title for w in ["portuguese", "portugal", "almeida", "vilhena", "sousa", "goncalo", "alvares"]):
        return "portuguese"
    if any(w in pers_title for w in ["sephardic", "jewish", "ben ", "mordecai", "isaac"]):
        return "sephardic"
    if any(w in pers_title for w in ["malian", "timbuktu", "mansa"]):
        return "malian"

    # Now check full combined (including location) for remaining cultures
    if any(w in combined for w in ["ottoman", "sultan", "edirne", "bey"]):
        return "ottoman"
    if any(w in combined for w in ["florentine", "medici", "florence", "tuscan", "strozzi"]):
        return "florentine"
    if any(w in combined for w in ["venetian", "venice", "contarini", "diedo", "duodo"]):
        return "venetian"
    if any(w in combined for w in ["genoese", "genoa", "lomellini", "fregoso", "fieschi", "adorno", "grimaldi"]):
        return "genoese"
    if any(w in combined for w in ["ferrara", "ferrarese", "d'este", "deste"]):
        return "ferrarese"
    if any(w in combined for w in ["sicil"]):
        return "sicilian"
    if any(w in combined for w in ["italian", "italy", "napl", "roman", "bolognese", "bentivoglio", "pallavicini", "gonzaga"]):
        return "italian"
    if any(w in combined for w in ["polish", "poland", "kraków", "szlachta"]):
        return "polish"
    if any(w in combined for w in ["hungarian", "hungary", "macsó"]):
        return "hungarian"
    # Byzantine/Constantinople — only if no other culture matched above
    if any(w in combined for w in ["byzantine", "palaiolog", "constantinople", "despot", "orthodox patriarch"]):
        return "byzantine"
    if any(w in combined for w in ["french", "breton", "france", "anjou"]):
        return "french"
    if any(w in combined for w in ["english", "england"]):
        return "english"
    if any(w in combined for w in ["german", "saxon"]):
        return "german"
    if any(w in combined for w in ["portuguese", "portugal", "lisbon", "sagres", "navigator"]):
        return "portuguese"
    if any(w in combined for w in ["catalan", "catalonia", "barcelona", "girona", "fiveller", "sant climent", "despujol", "pallars"]):
        return "catalan"
    if any(w in combined for w in ["aragonese", "aragon", "centelles", "bardaxi", "perellos", "vic"]):
        return "aragonese"

    # Default to Castilian for most characters
    return "castilian"


# ─── Build Determination ───

def get_build(gender, title, personality, born_year):
    """Generate build description from context."""
    age = REFERENCE_YEAR - born_year if born_year else 40
    title_lower = (title or "").lower()
    pers_str = " ".join(personality or []).lower()

    if age < 6:
        return "infant" if age < 2 else "small child"
    if age < 13:
        if "tall" in pers_str or "magnificent" in pers_str or "broad" in pers_str:
            return "tall and sturdy for a child"
        return "child, growing"
    if age < 18:
        return "adolescent, still growing"

    # Check personality for physical hints
    if "lean" in pers_str or "thin" in pers_str or "wiry" in pers_str:
        return "lean and wiry"
    if "stocky" in pers_str or "built like a bull" in pers_str or "broad" in pers_str:
        return "stocky and powerful"
    if "tall" in pers_str or "magnificent" in pers_str:
        return "tall and imposing"
    if "elderly" in pers_str or "aged" in pers_str or age > 60:
        if gender == "female":
            return "aged but dignified bearing"
        return "aged but carries himself with dignity"

    # Role-based
    # Banker / merchant checks BEFORE military to avoid "ban" matching "banco"
    if any(w in title_lower for w in ["banker", "merchant", "administrator", "banco", "principal"]):
        return "well-fed but carries himself with purpose"
    if any(w in title_lower for w in ["soldier", "knight", "captain", "commander", "sergeant", "military", "hetman", "ban of"]):
        if age > 50:
            return "broad-shouldered, weathered by years of campaign"
        return "broad-shouldered and hardened by campaign life"
    if any(w in title_lower for w in ["friar", "fray", "brother", "monk"]):
        return "lean from ascetic life"
    if any(w in title_lower for w in ["worker", "blacksmith", "craftsman"]):
        return "muscular from physical labor"

    # Age-based defaults
    if age > 55:
        return "carries age with quiet authority"
    if gender == "female":
        return "poised bearing"
    return "medium build, carries himself with the bearing of his station"


# ─── Facial Features ───

def get_facial_features(gender, personality, title):
    """Generate facial features from personality and role."""
    pers_str = " ".join(personality or []).lower()
    title_lower = (title or "").lower()

    features = []

    # Check for beauty markers
    if "beautiful" in pers_str or "legendary beauty" in pers_str:
        if gender == "female":
            features.append("strikingly beautiful features")
        else:
            features.append("handsome, well-proportioned features")
    elif "plain" in pers_str:
        features.append("plain but honest features")

    if "sharp" in pers_str or "calculating" in pers_str or "cunning" in pers_str:
        features.append("sharp, observant expression")
    if "warm" in pers_str or "kind" in pers_str or "gentle" in pers_str:
        features.append("warm expression, kind eyes")
    if "stern" in pers_str or "disciplined" in pers_str:
        features.append("stern, disciplined expression")
    if "hawk" in pers_str:
        features.append("hawk-like features, sharp attentive expression")
    if "gaunt" in pers_str:
        features.append("gaunt cheeks")

    if not features:
        # Role-based defaults
        if any(w in title_lower for w in ["soldier", "knight", "military", "captain"]):
            features.append("weathered face marked by sun and wind")
        elif any(w in title_lower for w in ["scholar", "theologian"]):
            features.append("thoughtful expression, high forehead")
        elif any(w in title_lower for w in ["friar", "priest", "brother"]):
            features.append("gentle features shaped by prayer and contemplation")
        elif "merchant" in title_lower or "banker" in title_lower:
            features.append("shrewd expression, attentive eyes")
        elif gender == "female":
            features.append("fine features with composed expression")
        else:
            features.append("strong features, measured expression")

    return ", ".join(features)


# ─── Hair Style ───

def get_hair(gender, culture_rules, personality, born_year, title):
    """Generate hair description."""
    import random
    random.seed(hash(title or "") + (born_year or 1400))

    age = REFERENCE_YEAR - born_year if born_year else 40
    base_color = random.choice(culture_rules["hair_colors"])
    title_lower = (title or "").lower()
    pers_str = " ".join(personality or []).lower()

    # Check for explicit hair mentions in personality
    if "dark hair" in pers_str:
        base_color = "dark"
    if "white" in pers_str and "hair" in pers_str:
        base_color = "white"

    # Tonsured religious
    if any(w in title_lower for w in ["friar", "fray", "brother", "monk", "abbot"]):
        if age > 50:
            return "tonsured, remaining hair white"
        return "tonsured, remaining hair " + base_color

    # Age modifiers
    if age > 60:
        base_color = "white"
    elif age > 50:
        base_color = base_color + ", greying"
    elif age > 40:
        base_color = base_color + ", touches of grey at temples"

    # Children
    if age < 10:
        return base_color + ", fine and soft"
    if age < 16:
        return base_color

    # Style based on gender and role
    if gender == "female":
        if any(w in title_lower for w in ["queen", "princess", "noblewoman", "lady"]):
            return base_color + ", worn in elaborate court style"
        if "servant" in title_lower or "attendant" in title_lower:
            return base_color + ", neatly pinned back"
        return base_color + ", neatly arranged"
    else:
        if any(w in title_lower for w in ["soldier", "knight", "captain", "military"]):
            return base_color + ", kept short and practical"
        if any(w in title_lower for w in ["nobleman", "count", "duke", "marquess"]):
            return base_color + ", neatly trimmed"
        return base_color + ", kept practical"

    return base_color


# ─── Eyes ───

def get_eyes(culture_rules, personality, title):
    """Generate eye description."""
    import random
    random.seed(hash(title or "") + 42)

    base_color = random.choice(culture_rules["eye_colors"])
    pers_str = " ".join(personality or []).lower()
    title_lower = (title or "").lower()

    # Check personality for eye descriptions
    if "grey-green" in pers_str:
        base_color = "grey-green"
    if "calculating" in pers_str:
        return base_color + ", calculating"
    if "observant" in pers_str or "watchful" in pers_str:
        return base_color + ", watchful and observant"
    if "sharp" in pers_str:
        return base_color + ", sharp and perceptive"
    if "warm" in pers_str:
        return base_color + ", warm and expressive"
    if "gentle" in pers_str or "kind" in pers_str:
        return base_color + ", gentle"
    if "penetrating" in pers_str:
        return base_color + ", penetrating gaze"
    if "passionate" in pers_str or "eager" in pers_str:
        return base_color + ", bright and eager"

    # Role-based
    if any(w in title_lower for w in ["soldier", "military", "captain"]):
        return base_color + ", steady and alert"
    if any(w in title_lower for w in ["scholar", "theologian"]):
        return base_color + ", thoughtful"
    if any(w in title_lower for w in ["merchant", "banker"]):
        return base_color + ", shrewd"

    return base_color + ", attentive"


# ─── Main Logic ───

def calculate_age(born_str):
    """Extract birth year from born field."""
    if not born_str:
        return None
    match = re.match(r"(\d{4})", born_str)
    return int(match.group(1)) if match else None


def build_appearance(char_id, char_data):
    """Generate a complete appearance dictionary for a character."""
    title = char_data.get("title", "")
    personality = char_data.get("personality", [])
    born_str = char_data.get("born", "")
    location = char_data.get("location", "")
    status = char_data.get("status", [])

    # Skip deceased characters — they don't need portraits
    if "deceased" in status:
        return None

    born_year = calculate_age(born_str)
    age = REFERENCE_YEAR - born_year if born_year else None

    gender = detect_gender(char_id, title)
    culture_key = detect_culture(char_id, title, personality, location)
    culture = CULTURE_RULES.get(culture_key, CULTURE_RULES["castilian"])

    # Age description
    if age is not None:
        pers_str = " ".join(personality).lower() if personality else ""
        if age < 2:
            age_desc = f"{age}, infant"
        elif age < 6:
            age_desc = f"{age}, small child"
        elif age < 13:
            age_desc = f"{age}, child"
        elif age < 18:
            age_desc = f"{age}, youth"
        elif age > 60:
            age_desc = f"{age}, elderly but still active"
        elif age > 50:
            if "vigorous" in pers_str or "capable" in pers_str:
                age_desc = f"{age}, vigorous despite the years"
            else:
                age_desc = f"{age}, weathered by years of service"
        else:
            age_desc = f"{age}, in the prime of life"
    else:
        age_desc = "middle-aged"

    build = get_build(gender, title, personality, born_year or (REFERENCE_YEAR - 40))
    hair = get_hair(gender, culture, personality, born_year or (REFERENCE_YEAR - 40), title)
    eyes = get_eyes(culture, personality, title)
    facial_features = get_facial_features(gender, personality, title)
    default_clothing, court_clothing, battle_clothing = get_clothing_for_role(title, personality, culture_key)

    # Override clothing for young children — they don't wear full royal/military attire
    if age is not None and age < 6:
        if gender == "female":
            default_clothing = "soft linen swaddling clothes" if age < 2 else "fine wool child's dress in muted colours"
        else:
            default_clothing = "soft linen swaddling clothes" if age < 2 else "fine wool child's tunic"
        court_clothing = "miniature court outfit befitting a child of rank" if age >= 3 else ""
        battle_clothing = ""
    elif age is not None and age < 13:
        title_lower_check = (title or "").lower()
        if "prince" in title_lower_check or "princess" in title_lower_check:
            if gender == "female":
                default_clothing = "fine wool dress in muted colours befitting a princess child"
                court_clothing = "miniature court gown with gold trim"
            else:
                default_clothing = "fine tunic with the arms of Castile, leather belt"
                court_clothing = "miniature doublet in royal colours"
            battle_clothing = ""

    # Distinguishing marks from personality
    marks = ""
    pers_str = " ".join(personality).lower() if personality else ""
    if "calloused" in pers_str:
        marks = "calloused hands"
    if "sun-darkened" in pers_str:
        marks = "sun-darkened hands and face"
    if "ink" in pers_str:
        marks = "ink-stained fingers"

    return {
        "gender": gender,
        "age_description": age_desc,
        "build": build,
        "hair": hair,
        "eyes": eyes,
        "skin": culture["skin"],
        "facial_features": facial_features,
        "distinguishing_marks": marks,
        "default_clothing": default_clothing,
        "court_clothing": court_clothing,
        "battle_clothing": battle_clothing,
        "art_style": culture["art_style"],
    }


def main():
    write_mode = "--write" in sys.argv
    force_mode = "--force" in sys.argv

    # Characters with hand-crafted appearance data that should not be overwritten
    HAND_CRAFTED = {
        "juan_ii", "lucia_deste", "catalina", "fernando",
        "alvaro_de_luna", "fray_hernando", "diego_de_daza", "isaac_de_baeza",
    }

    with open(ENRICHMENT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    added = 0
    skipped = 0
    already_has = 0

    for char_id, char_data in data.items():
        if char_id.startswith("_"):
            continue
        if not isinstance(char_data, dict):
            continue

        if "appearance" in char_data:
            if not force_mode or char_id in HAND_CRAFTED:
                already_has += 1
                continue
            # Force mode: regenerate non-hand-crafted appearances

        appearance = build_appearance(char_id, char_data)
        if appearance is None:
            skipped += 1
            continue

        char_data["appearance"] = appearance
        added += 1

    print(f"Characters with appearance: {already_has} (already had)")
    print(f"Characters enriched: {added}")
    print(f"Characters skipped (deceased): {skipped}")
    print(f"Total characters processed: {already_has + added + skipped}")

    if write_mode:
        with open(ENRICHMENT_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\nWritten to {ENRICHMENT_PATH}")
    else:
        print("\nDry run. Use --write to save changes.")

        # Show a few examples
        print("\n--- Example appearances ---")
        count = 0
        for char_id, char_data in data.items():
            if char_id.startswith("_") or not isinstance(char_data, dict):
                continue
            if "appearance" in char_data and char_id not in (
                "juan_ii", "lucia_deste", "alvaro_de_luna",
                "fray_hernando", "diego_de_daza", "isaac_de_baeza",
                "catalina", "fernando",
            ):
                print(f"\n{char_id}:")
                app = char_data["appearance"]
                for k, v in app.items():
                    if v:
                        print(f"  {k}: {v}")
                count += 1
                if count >= 5:
                    break


if __name__ == "__main__":
    main()
