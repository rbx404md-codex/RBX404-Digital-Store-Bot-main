"""Tiny i18n helper. Usage: `t("menu_store", lang)`.

Falls back to English for any key missing in the requested language, and
to the raw key itself if it's missing everywhere (so a typo shows up
visibly in testing instead of silently vanishing).
"""
from locales.strings import STRINGS, SUPPORTED_LANGUAGES


def t(key: str, lang: str = "bn", **kwargs) -> str:
    lang = lang if lang in SUPPORTED_LANGUAGES else "bn"
    text = STRINGS.get(lang, {}).get(key) or STRINGS["en"].get(key) or key
    return text.format(**kwargs) if kwargs else text
