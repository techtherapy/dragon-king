# Keeping the language versions in step

The site is published three times: English at the root, Spanish under `/es/`,
French under `/fr/`. They are not three projects. They are one site whose words
exist in three languages, and the build refuses to publish them out of step.

**The invariant:** *no change ships in one language only.*

You do not have to remember this. Three automated checks enforce it, and
`bash scripts/build_site.sh` runs them before it assembles anything — so a
half-translated change fails the build rather than reaching a reader.

---

## 1. Know which kind of page you are editing

Where you make a change depends on who produces the page. There are three
kinds, and only one of them is edited by hand in three places.

| Kind | Pages | Where to edit | How it stays in step |
|---|---|---|---|
| **Generated** | `read.html`, `treasure-vase-yoga.html` | the generator in `scripts/`, never the HTML | one template emits every language — structural drift is impossible |
| **Hand-authored** | `index`, `about`, `refuge`, `contact`, `his-holiness-…`, `treasure-vase-wishes`, `nagas-and-dragon-kings` | the English file **and** its twin in `es/` **and** in `fr/` | `check_translation_parity.py` fails the build if you touch one and not the others |
| **Shared** | `css/`, `js/`, `assets/` | once | every language loads the same files |

If you edit `treasure-vase-yoga.html` directly, your change is destroyed the
next time anyone runs the generator. Edit `scripts/build_practice.py`.

## 2. The three checks

Run any time: `python3 scripts/check_translation_parity.py`

**Structure.** Every hand-authored page must have an element sequence (tags +
classes, text ignored) identical to its English original, in every language.
Catches a section added, a class renamed, a block reordered in one language
only. The error names the file and language, both element counts, and the exact
index where they diverge.

**Text.** `translations/parity.json` records a hash of each page's visible words
per language. If the English text changes and a translation does not, the build
fails — this is the drift structure alone cannot see, such as rewording a
sentence. After translating the change, re-record:

```bash
python3 scripts/check_translation_parity.py --record
```

Committing the refreshed `parity.json` is part of the change.

**Generator strings.** The string tables inside `build_practice.py` (`UI`,
`CAPTIONS`) must define the same keys in every language, so a new label cannot
ship in English with nothing behind it in Spanish or French.
`build_reader.py` guards itself twice over: its `CHROME_TR` table pairs each
English pattern with a replacement for *every* language and refuses at import
time if one is missing, and `to_lang()` raises if a pattern it expects to
translate is not found — so a reworded English chrome string fails loudly
instead of silently staying English.

Content in the generated pages is guarded by count, not hash: `build_reader.py`
refuses to build if any chapter's translated verse count differs from the
source, and `build_practice.py` does the same for the transcript's paragraph and
heading sequence.

## 3. Recipes

**Change a sentence on a hand-authored page**
1. Edit the English file, `es/<same-name>` and `fr/<same-name>`.
2. `python3 scripts/check_translation_parity.py --record`
3. `bash scripts/build_site.sh`

**Change something on a generated page** — edit the generator only. Text in its
`UI`/`CAPTIONS` tables, transcript wording via the normalisers in
`paragraphs()` (never the recordings in `extra-content/`, which stay as
transcribed), then rerun the generator. Every language updates together.

**Change the shared chrome** (nav, footer) — it lives in four places: the seven
hand-authored English pages, their `es/` and `fr/` twins, `build_reader.py`'s
`CHROME_HEAD`/`CHROME_FOOT` plus its `CHROME_TR` translation table, and
`build_practice.py`, which lifts its chrome from `refuge.html` in each language
so it follows automatically. Change the pages first, then rerun both generators.

**Add a page**
1. Write `newpage.html`, `es/newpage.html` and `fr/newpage.html` (the
   translations use root-absolute asset paths — `/css/…`, `/assets/…` — and
   link to their own language's twins).
2. Add the switcher group to all three navs, each listing the other two
   languages.
3. Add it to `PAIRS` in `check_translation_parity.py` and to `PAGES` in
   `add_seo.py` (which gives it canonical, hreflang and sitemap entries).
4. `python3 scripts/check_translation_parity.py --record`

**Add a language.** The machinery takes a list of language codes rather than a
hardcoded pair, so this is mostly data entry:

1. `LANGS` in `check_translation_parity.py`, `add_seo.py` (plus `OG_LOCALE` and
   a `CRUMBS` entry) and `build_practice.py`.
2. `LAYERS` in `build_reader.py`, and a replacement for the new language on
   every entry of `CHROME_TR` — the import-time check tells you if you miss one.
3. `LAYERS` and `DEFAULTS` in `js/reader.js`; a `.prow .<class>` rule and a
   `body.hide-<code>` rule in `css/reader.css`, plus the new class in the
   `:not(...)` negations that keep the English title lines from vanishing.
4. `OFFERS` in `js/main.js`, so the banner can offer it in its own words.
5. A `UI`/`CAPTIONS` table in `build_practice.py`.
6. The language directory in `scripts/build_site.sh`.
7. `translations/<code>/` — 20 chapter files, `common.json` and the two practice
   transcripts, verse- and item-aligned to `translations/src/`.
8. The hand-authored pages, and one more link in every switcher group.

The invariant and the three checks carry over unchanged.

## 4. Translation conventions

Keep these stable — the checks enforce *presence*, not *wording*.

### Common to both translations

- Untranslated everywhere: `Dragon King Sutra` (the wordmark), `True Buddha
  School`, other sites' names, all 漢字, pinyin, and personal names
  (Sheng-Yen Lu, Janny Chow, Dharmaraksa, Lian Sheng).
- Anchor ids are slugged from the **English** headings in every language, so a
  deep link works whichever version the reader opens. Never localise an id.
- Sanskrit loanwords stay unaccented and unitalicised: nagas, bodhisattva,
  asura, garuda, kalpa, dharani, devas.
- Lowercase mid-sentence, matching English house style: *dharma* and the
  language's word for buddhahood.

### Spanish

- Latin American Spanish; **ustedes**, never *vosotros*.
- `Living Buddha Lian Sheng` → *el Buda Viviente Lian Sheng* in prose,
  *Buda Viviente Lian Sheng* as a bare nav label.
- *el Honrado por el Mundo*, *el Rey Dragón del Mar*, *el Jarrón del Tesoro*,
  *el Gran Maestro*, *budeidad*.
- Mantras: `Om Guru Lian Sheng Sidi Jom`; the Dragon King mantra ends
  *wad-lli-la, mi*.

### French

- Standard French; **vous** throughout, never *tu* — including where the Buddha
  addresses a character, for a register that reads aloud with dignity.
- Normal space before `:` `;` `!` `?` (not a narrow no-break space). French
  guillemets « … » for quoted speech, with `“ … ”` nested inside. Straight
  apostrophes `'`, matching the rest of the codebase.
- `Living Buddha Lian Sheng` → *le Bouddha Vivant Lian Sheng* in prose,
  *Bouddha Vivant Lian Sheng* as a bare nav label; *S.S.* for His Holiness.
- *le Vénéré du Monde*, *le Roi Dragon de la Mer*, *le Pic des Vautours*,
  *le Palais du Dragon*, *le Grand Maître*, *bouddhéité*, *bouddhadharma*,
  *soutra* (m.), *bhikshus*.
- *le Vase du Trésor* for 寶瓶, so *Le Yoga du Vase du Trésor du Roi Dragon*.
- Feminine **la dharani**, *les dharanis* — Sanskrit *dhāraṇī* is feminine and
  that is standard French Buddhist usage.
- Settled renderings, chosen because twenty parallel translators each picked
  differently: *la quiétude finale* (final quiescence), *l'apaisement /
  paisible* (stillness), *la sphère du dharma* (dharma-realm), *l'éveil
  insurpassable, juste et véritable* (unsurpassed, right and true
  enlightenment), *la prédiction* (the Prediction), *le mérite*.
- Temple names are translated (*Temple de l'Arc-en-ciel*, *Temple Leizang de
  Seattle*); sister-site names are not.
- Mantras: `Om Gourou Lian Sheng Siddhi Houm`; the Dragon King mantra is
  *Namo sam-man-do, mou-to-nam, wadjila, mi*.

## 5. Honest limits

- The text check notices *that* English changed without a translation. It cannot
  tell whether an accompanying edit was the *right* translation, or even
  related. It is a reminder, not a reviewer.
- Editing every language in the same commit always passes, even if a translation
  is wrong. Correctness still needs a reader who speaks the language.
- Both translations are machine translation held to the glossaries above,
  and both are second-hand: they were made from the English, which is itself a
  translation of the Chinese. Neither has had a native-speaker review. Treat
  them as good working copy rather than canonical liturgy until they do.
- The Spanish layer renders *dharani* inconsistently (37 feminine, 20
  masculine). The French was normalised to feminine throughout; the Spanish has
  not been, and would need the same pass.
