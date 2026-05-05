try:
    from deep_translator import GoogleTranslator
except Exception:
    GoogleTranslator = None


class TranslationServiceError(Exception):
    pass


def translate_text(text, source_language='en', target_language='mr', fail_silently=True):
    value = (text or '').strip()
    if not value:
        return ''

    if GoogleTranslator is None:
        if fail_silently:
            return value
        raise TranslationServiceError('Free translator dependency is not installed. Run: pip install deep-translator')

    try:
        translated = GoogleTranslator(source=source_language, target=target_language).translate(value)
    except Exception as exc:
        if fail_silently:
            return value
        raise TranslationServiceError(f'Free translation service failed: {exc}') from exc

    return (translated or '').strip()
