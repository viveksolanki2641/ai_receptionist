from deep_translator import GoogleTranslator
from langdetect import detect

def detected_que_language(user_query: str) -> str:
    # Detect the language using langdetect
    detected_language = detect(user_query)
    print(f"Detected language: {detected_language}")
    return detected_language

def convert_language(user_query: str, current_language: str, dest_language: str):
    """
    Convert the user's query from the detected language to the target language.
    If the current or destination language is not English, Hindi, or Gujarati, it defaults to English.
    """
    # Define allowed languages
    allowed_languages = ['en', 'hi', 'gu']

    # If current_language is not in allowed languages, set it to English
    if current_language not in allowed_languages:
        current_language = 'en'

    # If dest_language is not in allowed languages, set it to English
    if dest_language not in allowed_languages:
        dest_language = 'en'

    # Translate the query using Google Translator
    translated_query = GoogleTranslator(source=current_language, target=dest_language).translate(user_query)
    print(f"Translated query to {dest_language}: {translated_query}")
    return translated_query