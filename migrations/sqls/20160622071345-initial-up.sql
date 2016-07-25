CREATE TABLE languages (
    language_id SERIAL PRIMARY KEY,
    language_code VARCHAR NOT NULL UNIQUE,  -- ISO 639-1
    name VARCHAR NOT NULL UNIQUE
);

CREATE TABLE countries (
    country_id SERIAL PRIMARY KEY,
    country_code VARCHAR NOT NULL UNIQUE,  -- ISO 3166-1 alpha-2 
    name VARCHAR NOT NULL UNIQUE
);

CREATE TABLE translations (
    translation_id SERIAL PRIMARY KEY,
    translation_key VARCHAR NOT NULL,
    language_id INTEGER NOT NULL REFERENCES languages,
    country_id INTEGER DEFAULT NULL REFERENCES countries,
    plural INTEGER DEFAULT NULL,
    translation_text VARCHAR DEFAULT NULL
);

CREATE UNIQUE INDEX translations_key_language_unique_idx ON
    translations (translation_key, language_id)
WHERE country_id IS NULL AND plural IS NULL;

CREATE UNIQUE INDEX translations_key_language_country_unique_idx ON
    translations (translation_key, language_id, country_id)
WHERE country_id IS NOT NULL AND plural IS NULL;

CREATE UNIQUE INDEX translations_key_language_plural_unique_idx ON
    translations (translation_key, language_id, plural)
WHERE country_id IS NULL AND plural IS NOT NULL;

CREATE UNIQUE INDEX translations_key_language_country_plural_unique_idx ON
    translations (translation_key, language_id, country_id, plural)
WHERE country_id IS NOT NULL AND plural IS NOT NULL;
