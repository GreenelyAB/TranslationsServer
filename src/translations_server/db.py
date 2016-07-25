# -*- coding: utf-8 -*-
from translations_server.lib import db


_get_translation = db.SelectOne('''
    SELECT COALESCE(translation_text, translation_key)
    FROM translations
    JOIN languages USING (language_id)
    LEFT JOIN countries USING (country_id)
    WHERE
        language_code = %s AND (country_code IS NULL OR country_code = %s) AND
        translation_key = %s AND
        ((%s = '%%' AND plural IS NULL) OR plural = %s)
    ORDER BY country_code ASC -- existing country comes first
    LIMIT 1
''')


def get_translation(lang, country, key, plural):
    """
    :type lang: str
    :type country: str
    :type key: str
    :type plural: int or None
    :rtype: str or None
    """
    return _get_translation(
        lang, country or None, key, "%" if plural is None else 'x',
        plural)


# The following SQL statements are used by tests.
_insert_translation = db.Manipulation('''
INSERT INTO translations
    (translation_key, language_id, country_id, plural, translation_text)
VALUES (%s, %s, %s, %s, %s)
''')

_insert_language = db.SelectOne('''
    INSERT INTO languages (language_id, language_code, name)
    VALUES (DEFAULT, %s, %s)
    RETURNING language_id
''')

_insert_country = db.SelectOne('''
    INSERT INTO countries (country_id, country_code, name)
    VALUES (DEFAULT, %s, %s)
    RETURNING country_id
''')
