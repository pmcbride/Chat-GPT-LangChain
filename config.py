from dotenv import load_dotenv
load_dotenv()

import os

__all__ = [
    "NEWS_API_KEY",
    "TMDB_BEARER_TOKEN",
    "TOOLS_LIST",
    "TOOLS_DEFAULT_LIST",
    "BUG_FOUND_MSG",
    "AUTH_ERR_MSG",
    "MAX_TOKENS",
    "LOOPING_TALKING_HEAD",
    "TALKING_HEAD_WIDTH",
    "MAX_TALKING_HEAD_TEXT_LENGTH",
    "NUM_WORDS_DEFAULT",
    "MAX_WORDS",
    "FORMALITY_DEFAULT",
    "TEMPERATURE_DEFAULT",
    "EMOTION_DEFAULT",
    "LANG_LEVEL_DEFAULT",
    "TRANSLATE_TO_DEFAULT",
    "LITERARY_STYLE_DEFAULT",
    "FORCE_TRANSLATE_DEFAULT",
    "USE_GPT4_DEFAULT",
    "TRANSLATE_TO_LANGS",
    "TRANSLATE_TO_DEFAULT_LANGS",
    "WHISPER_DETECT_LANG",
    "WHISPER_LANGS",
    "WHISPER_DEFAULT_LANGS",
    "LANG_LEVELS",
    "LANG_DEFAULT_LEVELS",
    "LITERARY_STYLES",
    "LITERARY_DEFAULT_STYLES",
]

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
TMDB_BEARER_TOKEN = os.getenv("TMDB_BEARER_TOKEN")

TOOLS_LIST = [
    "serpapi",
    "google-search",
    "requests_all",
    "wolfram-alpha",
    "pal-math",
    "pal-colored-objects",
    "news-api",
    "tmdb-api",
    # 'open-meteo-api'
]
TOOLS_DEFAULT_LIST = [
    "serpapi",
    "requests_all", 
    # "google-search",
    "wolfram-alpha",
    "pal-math"
]
BUG_FOUND_MSG = "Congratulations, you've found a bug in this application!"
# AUTH_ERR_MSG = "Please paste your OpenAI key from openai.com to use this application. It is not necessary to hit a button or key after pasting it."
AUTH_ERR_MSG = "Please paste your OpenAI key from openai.com to use this application. "
MAX_TOKENS = 512

LOOPING_TALKING_HEAD = "videos/Masahiro.mp4"
TALKING_HEAD_WIDTH = "192"
MAX_TALKING_HEAD_TEXT_LENGTH = 155

# Pertains to Express-inator functionality
NUM_WORDS_DEFAULT = 0
MAX_WORDS = 400
FORMALITY_DEFAULT = "N/A"
TEMPERATURE_DEFAULT = 0.5
EMOTION_DEFAULT = "N/A"
LANG_LEVEL_DEFAULT = "N/A"
TRANSLATE_TO_DEFAULT = "N/A"
LITERARY_STYLE_DEFAULT = "N/A"


# Translate To languages available
TRANSLATE_TO_LANGS = [
    "Arabic", "Arabic (Gulf)", "Catalan", "Chinese (Cantonese)", "Chinese (Mandarin)",
    "Danish", "Dutch", "English (Australian)", "English (British)", "English (Indian)", "English (New Zealand)",
    "English (South African)", "English (US)", "English (Welsh)", "Finnish", "French", "French (Canadian)",
    "German", "German (Austrian)", "Georgian", "Hindi", "Icelandic", "Indonesian", "Italian", "Japanese",
    "Korean", "Norwegian", "Polish",
    "Portuguese (Brazilian)", "Portuguese (European)", "Romanian", "Russian", "Spanish (European)",
    "Spanish (Mexican)", "Spanish (US)", "Swedish", "Turkish", "Ukrainian", "Welsh"]
TRANSLATE_TO_DEFAULT_LANGS = [
    "English (US)",
    "Chinese (Mandarin)",
]


# Pertains to WHISPER functionality
WHISPER_DETECT_LANG = "Detect language"
WHISPER_LANGS = [
    "Arabic", "Arabic (Gulf)", "Catalan", "Chinese (Cantonese)", "Chinese (Mandarin)",
    "Danish", "Dutch", "English (Australian)", "English (British)", "English (Indian)", "English (New Zealand)",
    "English (South African)", "English (US)", "English (Welsh)", "Finnish", "French", "French (Canadian)",
    "German", "German (Austrian)", "Georgian", "Hindi", "Icelandic", "Indonesian", "Italian", "Japanese",
    "Korean", "Norwegian", "Polish",
    "Portuguese (Brazilian)", "Portuguese (European)", "Romanian", "Russian", "Spanish (European)",
    "Spanish (Mexican)", "Spanish (US)", "Swedish", "Turkish", "Ukrainian", "Welsh",
    "emojis", "Gen Z slang", "how the stereotypical Karen would say it", "Klingon", "Neanderthal",
    "Pirate", "Strange Planet expospeak technical talk", "Yoda"]
WHISPER_DEFAULT_LANGS = [
    "English (US)",
    "Chinese (Mandarin)",
]


# Lang Level languages available
LANG_LEVELS = [
    "N5 (beginner)", "N4 (basic)", "N3 (intermediate)", "N2 (proficient)", "N1 (advanced)",
    "1st grade", "2nd grade", "3rd grade", "4th grade", "5th grade", "6th grade",
    "7th grade", "8th grade", "9th grade", "10th grade", "11th grade", "12th grade", "University"]
LANG_DEFAULT_LEVELS = [
    "N5 (beginner)", "N4 (basic)", "N3 (intermediate)", "N2 (proficient)", "N1 (advanced)", 
    "High School", "University", "Graduate School"
]

# Lit Style languages available
LITERARY_STYLES = [
    "Prose", "Story", "Summary", "Outline", "Bullets", 
    "Poetry", "Haiku", "Limerick", "Rap", "Joke", "Knock-knock", "FAQ"]
LITERARY_DEFAULT_STYLES = [
    "Prose",
    "Story",
    "Summary",
    "Outline",
    "Bullets",
    "FAQ"
]

FORCE_TRANSLATE_DEFAULT = False  # TODO: Change back to True?
USE_GPT4_DEFAULT = False