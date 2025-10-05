"""
Sake Sensei - Preference Converter

Convert between Japanese UI preferences and backend format.
"""


def convert_to_display_format(preferences: dict) -> dict:
    """
    Convert backend preferences to Japanese UI format.

    Args:
        preferences: Preferences in backend format

    Returns:
        Preferences in Japanese UI format
    """
    # Reverse mapping for sweetness (1-5 to Japanese)
    sweetness_reverse = {
        1: "とても甘口",
        2: "甘口",
        3: "中口",
        4: "辛口",
        5: "とても辛口",
    }

    # Reverse mapping for richness/body (1-5 to Japanese)
    body_reverse = {
        1: "とても軽い",
        2: "軽い",
        3: "中程度",
        4: "重い",
        5: "とても重い",
    }

    # Reverse mapping for experience level
    experience_reverse = {
        "beginner": "月に1回程度",
        "intermediate": "月に2-3回",
        "advanced": "ほぼ毎日",
    }

    # Reverse mapping for budget to price range
    budget = preferences.get("budget", 2500)
    if budget <= 1000:
        price_range = "～1,000円"
    elif budget <= 2000:
        price_range = "1,000～2,000円"
    elif budget <= 3000:
        price_range = "2,000～3,000円"
    elif budget <= 5000:
        price_range = "3,000～5,000円"
    else:
        price_range = "5,000円～"

    # Reverse mapping for sake types (English to Japanese)
    sake_type_reverse = {
        "junmai": "純米酒",
        "junmai_ginjo": "純米吟醸",
        "junmai_daiginjo": "純米大吟醸",
        "honjozo": "本醸造",
        "ginjo": "吟醸",
        "daiginjo": "大吟醸",
        "tokubetsu_junmai": "特別純米",
        "tokubetsu_honjozo": "特別本醸造",
    }

    return {
        "sake_types": [sake_type_reverse.get(t, t) for t in preferences.get("categories", [])],
        "sweetness": sweetness_reverse.get(preferences.get("sweetness", 3), "中口"),
        "body": body_reverse.get(preferences.get("richness", 3), "中程度"),
        "price_range": price_range,
        "experience_level": experience_reverse.get(
            preferences.get("experience_level", "beginner"), "月に1回程度"
        ),
        # Fields not stored in backend but needed for UI
        "aroma_preference": preferences.get("aroma_preference", []),
        "drinking_scene": preferences.get("drinking_scene", []),
        "food_pairing": preferences.get("food_pairing", []),
        "temperature_preference": preferences.get("temperature_preference", []),
        "knowledge_level": preferences.get("knowledge_level", "初心者"),
        "other_preferences": preferences.get("other_preferences", ""),
    }


def convert_to_backend_format(preferences: dict) -> dict:
    """
    Convert Japanese UI preferences to backend format.

    Args:
        preferences: Preferences in Japanese UI format

    Returns:
        Preferences in backend format
    """
    # Sweetness mapping (Japanese to 1-5 scale)
    sweetness_map = {
        "とても甘口": 1,
        "甘口": 2,
        "やや甘口": 2,
        "中口": 3,
        "やや辛口": 4,
        "辛口": 4,
        "とても辛口": 5,
    }

    # Body mapping (Japanese to 1-5 scale for richness)
    body_map = {
        "とても軽い": 1,
        "軽い": 2,
        "やや軽い": 2,
        "中程度": 3,
        "やや重い": 4,
        "重い": 4,
        "とても重い": 5,
    }

    # Experience level mapping
    experience_map = {
        "初めて": "beginner",
        "月に1回程度": "beginner",
        "月に2-3回": "intermediate",
        "週に1回以上": "intermediate",
        "ほぼ毎日": "advanced",
    }

    # Price range to budget mapping (use middle value)
    price_map = {
        "～1,000円": 1000,
        "1,000～2,000円": 1500,
        "2,000～3,000円": 2500,
        "3,000～5,000円": 4000,
        "5,000円～": 6000,
    }

    # Sake type mapping (Japanese to English)
    sake_type_map = {
        "純米酒": "junmai",
        "純米吟醸": "junmai_ginjo",
        "純米大吟醸": "junmai_daiginjo",
        "本醸造": "honjozo",
        "吟醸": "ginjo",
        "大吟醸": "daiginjo",
        "特別純米": "tokubetsu_junmai",
        "特別本醸造": "tokubetsu_honjozo",
    }

    return {
        "categories": [sake_type_map.get(t, t) for t in preferences.get("sake_types", [])],
        "sweetness": sweetness_map.get(preferences.get("sweetness", "中口"), 3),
        "richness": body_map.get(preferences.get("body", "中程度"), 3),
        "budget": price_map.get(preferences.get("price_range", "2,000～3,000円"), 2500),
        "experience_level": experience_map.get(
            preferences.get("experience_level", "初めて"), "beginner"
        ),
        "avoid_categories": [],  # Not collected in current UI
    }
