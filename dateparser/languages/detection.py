# -*- coding: utf-8 -*-
from functools import wraps

from dateparser.languages import LanguageDataLoader

default_language_loader = LanguageDataLoader()


def _restore_languages_on_generator_exit(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        stored_languages = self.languages[:]
        for language in method(self, *args, **kwargs):
            yield language
        else:
            self.languages[:] = stored_languages

    return wrapped


class BaseLanguageDetector(object):
    def __init__(self, languages):
        self.languages = languages

    @_restore_languages_on_generator_exit
    def iterate_applicable_languages(self, date_string, modify=False):
        languages = self.languages if modify else self.languages[:]
        for language in self._filter_languages(date_string, languages):
            yield language

    @staticmethod
    def _filter_languages(date_string, languages):
        while languages:
            language = languages[0]
            if language.is_applicable(date_string, strip_timezone=False):
                yield language
            elif language.is_applicable(date_string, strip_timezone=True):
                yield language

            languages.pop(0)


class AutoDetectLanguage(BaseLanguageDetector):
    def __init__(self, languages=None, allow_redetection=False):
        if languages is None:
            languages = default_language_loader.get_languages()
        super(AutoDetectLanguage, self).__init__(languages=languages)
        self.allow_redetection = allow_redetection

    @_restore_languages_on_generator_exit
    def iterate_applicable_languages(self, date_string, modify=False):
        languages = self.languages if modify else self.languages[:]
        initial_languages = languages[:]
        for language in self._filter_languages(date_string, languages):
            yield language

        if not self.allow_redetection:
            return

        # Try languages that was not tried before with this date_string
        languages = [language
                     for language in default_language_loader.get_languages()
                     if language not in initial_languages]
        if modify:
            self.languages = languages

        for language in self._filter_languages(date_string, languages):
            yield language


class ExactLanguages(BaseLanguageDetector):
    def __init__(self, languages):
        if languages is None:
            raise ValueError("language cannot be None for ExactLanguages")
        super(ExactLanguages, self).__init__(languages=languages)

    @_restore_languages_on_generator_exit
    def iterate_applicable_languages(self, date_string, modify=False):
        for language in super(
                ExactLanguages, self).iterate_applicable_languages(date_string, modify=False):
            yield language
