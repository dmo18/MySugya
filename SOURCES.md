# Yoma App — Sources

## Primary Text Sources

### Hebrew Talmud Text
- **Source:** Sefaria (sefaria.org)
- **API:** `https://www.sefaria.org/api/texts/Yoma.Xa?context=0` — `he[]` array
- **Basis:** The Vilna edition of the Babylonian Talmud (Romm Publishing House, Vilna, 1880–1886)
- **All `he:` fields** in learning_data.js are copied verbatim from Sefaria's `he[]` array (sourced from source_store.js), verified programmatically via `npm run validate`

### English Translation
- **Source:** Sefaria (sefaria.org)
- **Translation:** William Davidson Talmud (Koren Publishers Jerusalem), English translation by Rabbi Adin Even-Israel Steinsaltz
- **API:** same call — `text[]` array (parallel indices to `he[]`)
- **All `en:` fields** in learning_data.js are copied verbatim from Sefaria's `text[]` array at matching indices

## Layout Reference

### Vilna Edition Line Positions
- **Source:** talmud.dev API (`https://www.talmud.dev/api/daf/Yoma/<daf>`)
- **Tool:** `scripts/fetch_talmuddev.py` — fetches Gemara text in exact Vilna print order with `\r\n` per column line; cached to `assets/talmuddev/<daf>.json`
- **The Vilna edition** (Romm, Vilna, 1880–1886) is the standard printed edition used in virtually all Talmud study worldwide; its pagination is the universal reference
- Line positions are stored as `vilna_line` fields in learning_data.js and rendered as margin numbers in the app

## Technology

| Component | Source / License |
|-----------|-----------------|
| React | Meta (Facebook), MIT license, loaded via CDN |
| Babel | Babel team, MIT license, loaded via CDN |
| Python HTTP server | Python standard library |
| cwebp | Google WebP tools |

## Talmud Attribution Note

The Babylonian Talmud was compiled by the Amoraim and Stammaim in Babylonia, redacted approximately 200–600 CE. The Vilna edition printing (1880–1886) is in the public domain. Rashi (Rabbi Shlomo Yitzchaki, 1040–1105 CE) wrote his commentary in France; it is also in the public domain. The William Davidson Talmud English translation is © Koren Publishers Jerusalem; it is reproduced here via Sefaria's open-access API under Sefaria's terms of service for non-commercial, educational use.
