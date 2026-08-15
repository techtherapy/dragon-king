# Keeping the two language versions in step

The site is published twice: English at the root and Spanish under `/es/`.
They are not two projects. They are one site whose words exist in two
languages, and the build refuses to publish them out of step.

**The invariant:** *no change ships in one language only.*

You do not have to remember this. Three automated checks enforce it, and
`bash scripts/build_site.sh` runs them before it assembles anything — so a
half-translated change fails the build rather than reaching a reader.

---

## 1. Know which kind of page you are editing

Where you make a change depends on who produces the page. There are three
kinds, and only one of them is edited by hand in two places.

| Kind | Pages | Where to edit | How it stays in step |
|---|---|---|---|
| **Generated** | `read.html`, `treasure-vase-yoga.html` | the generator in `scripts/`, never the HTML | one template emits both languages — structural drift is impossible |
| **Hand-authored** | `index`, `about`, `refuge`, `contact`, `his-holiness-…`, `treasure-vase-wishes` | the English file **and** its twin in `es/` | `check_es_parity.py` fails the build if you touch one and not the other |
| **Shared** | `css/`, `js/`, `assets/` | once | both languages load the same files |

If you edit `treasure-vase-yoga.html` directly, your change is destroyed the
next time anyone runs the generator. Edit `scripts/build_practice.py`.

## 2. The three checks

Run any time: `python3 scripts/check_es_parity.py`

**Structure.** Every hand-authored pair must have an identical element
sequence (tags + classes, text ignored). Catches a section added, a class
renamed, a block reordered on one side only. The error names the file, both
element counts, and the exact index where they diverge.

**Text.** `translations/parity.json` records a hash of each page's visible
words per language. If the English text changes and the Spanish does not,
the build fails — this is the drift structure alone cannot see, such as
rewording a sentence. After translating the change into `es/`, re-record:

```bash
python3 scripts/check_es_parity.py --record
```

Committing the refreshed `parity.json` is part of the change.

**Generator strings.** The bilingual tables inside `build_practice.py`
(`UI`, `CAPTIONS`) must define the same keys in both languages, so a new
label cannot ship in English with nothing behind it in Spanish.
`build_reader.py` guards itself differently: its `CHROME_ES` table raises if
any pattern it expects to translate is not found, so a reworded English
chrome string fails loudly instead of silently staying English.

Content in the generated pages is guarded by count, not hash:
`build_reader.py` refuses to build if any chapter's Spanish verse count
differs from the source, and `build_practice.py` does the same for the
transcript's paragraph and heading sequence.

## 3. Recipes

**Change a sentence on a hand-authored page**
1. Edit the English file and `es/<same-name>`.
2. `python3 scripts/check_es_parity.py --record`
3. `bash scripts/build_site.sh`

**Change something on a generated page** — edit the generator only. Text in
its `UI`/`CAPTIONS` tables, transcript wording via the normalisers in
`paragraphs()` (never the recordings in `extra-content/`, which stay as
transcribed), then rerun the generator. Both languages update together.

**Change the shared chrome** (nav, footer) — it lives in five places: the
six hand-authored English pages, their `es/` twins, `build_reader.py`'s
`CHROME_HEAD`/`CHROME_FOOT` and its `CHROME_ES` translation table, and
`build_practice.py`, which lifts its chrome from `refuge.html` and
`es/refuge.html` so it follows automatically. Change the pages first, then
rerun both generators.

**Add a page**
1. Write `newpage.html` and `es/newpage.html` (Spanish uses root-absolute
   asset paths — `/css/…`, `/assets/…` — and links to `/es/…` twins).
2. Add the switcher link to both navs, each pointing at the other.
3. Add it to `PAIRS` in `check_es_parity.py` and to `PAGES` in
   `add_seo.py` (which gives it canonical, hreflang and sitemap entries).
4. `python3 scripts/check_es_parity.py --record`

**Adding a third language** (say Chinese at `/zh/`): the mechanism is not
hardcoded to Spanish in spirit, but it is in its names. Generalising means
turning `check_es_parity.py`'s single `es` into a list of language codes,
adding a `CHROME_ZH` table beside `CHROME_ES`, giving `UI`/`CAPTIONS` a
third key, and extending `add_seo.py`'s hreflang set. The invariant and the
three checks carry over unchanged.

## 4. Translation conventions

Keep these stable — the checks enforce *presence*, not *wording*.

- Latin American Spanish; **ustedes**, never *vosotros*.
- Untranslated: `Dragon King Sutra` (the wordmark), `True Buddha School`,
  other sites' names, all 漢字, and mantras except where a Spanish
  transliteration was specified (`Om Guru Lian Sheng Sidi Jom`; the Dragon
  King mantra ends *wad-lli-la, mi* in Spanish, *wajila, mee* in English).
- `Living Buddha Lian Sheng` → *el Buda Viviente Lian Sheng* in prose,
  *Buda Viviente Lian Sheng* as a bare nav label.
- Lowercase mid-sentence: *dharma*, *budeidad*, matching English house style.
- Anchor ids are slugged from the **English** headings in both languages, so
  a deep link works whichever version the reader opens. Never localise an id.

## 5. Honest limits

- The text check notices *that* English changed without Spanish. It cannot
  tell whether an accompanying Spanish edit was the *right* translation, or
  even related. It is a reminder, not a reviewer.
- Editing both languages in the same commit always passes, even if the
  Spanish is wrong. Correctness still needs a reader who speaks Spanish.
- The Spanish text is machine translation held to the glossary above. It has
  not had a native-speaker review; treat it as good working copy rather than
  canonical liturgy until it does.
