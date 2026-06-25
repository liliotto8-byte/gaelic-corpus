import os, re, glob, unicodedata

input_dir = "/content/Gaelic_txt/"
raw_path = "/content/gaelic_raw_clean.txt"
content_path = "/content/gaelic_content.txt"
lexicon_path = "hunspell-gd/clann.txt"
exclude_dwelly = True

acute_to_grave = str.maketrans("áéíóúÁÉÍÓÚ", "àèìòùÀÈÌÒÙ")
def normalize(text):
    return unicodedata.normalize("NFC", text).translate(acute_to_grave).lower()

def clean_basic(text):
    text = re.sub(r"[^a-zàèìòù\s]", " ", normalize(text))
    return re.sub(r"\s+", " ", text).strip()

vowels = set("aeiouàèìòù")
def looks_real(w):
    return 2 <= len(w) <= 20 and any(c in vowels for c in w)

gaelic_markers = set("""agus is an am na nan nam tha bha bidh robh eil ann air gu gus do de le ri
ach cha chan gun gum mar nuair seo sin mi thu sinn sibh iad mo dha dhan
bhith bhi gach uile aon comhla anns san fhuair rinn thainig""".split())
english_markers = set("""the and of to in a is that it was for with as his he on be at by i this
you are not or from they but had have which one all were her she there""".split())

def is_gaelic_paragraph(text):
    toks = clean_basic(text).split()
    if len(toks) < 5:
        return False
    g = sum(t in gaelic_markers for t in toks)
    e = sum(t in english_markers for t in toks)
    return g > 0 and g >= e

def split_paragraphs(text):
    chunks = []
    for block in re.split(r"\n\s*\n", text):
        words = block.split()
        for i in range(0, len(words), 60):
            chunks.append(" ".join(words[i:i+60]))
    return chunks

lenited = re.compile(r"^([bcdfgmpst])h(.+)$")
def delenite(w):
    m = lenited.match(w)
    return m.group(1) + m.group(2) if m else w

suffixes = ["annan","achan","ichean","ean","an","aich","ich","idh","aidh","eadh","adh","te","e","a"]

def load_lexicon(path):
    lex = set()
    for line in open(path, encoding="utf-8"):
        w = normalize(re.split(r"[\s,;/\t]", line.strip())[0])
        if len(w) > 1 and re.fullmatch(r"[a-zàèìòù]+", w):
            lex.add(w)
    return lex

lexicon = load_lexicon(lexicon_path) if os.path.exists(lexicon_path) else set()

def lemmatize(w):
    d = delenite(w)
    if not lexicon:
        return d
    for suf in suffixes:
        if d.endswith(suf) and len(d) - len(suf) >= 3 and d[:len(d)-len(suf)] in lexicon:
            return d[:len(d)-len(suf)]
    return d

stopwords = set("""a an am na nan nam airson nuair son cho
agus is no ach oir ma mur nach gun gum neo
air ann an le do de gu gus bho o ri ro tro
fo eadar mu aig as os fa seach ged
mi thu e i sinn sibh iad mise thusa esan ise sinne sibhse iadsan
mo do a ar ur
seo sin siud sineach seothach so
tha bha bidh bhios robh eil bi bhith ta th bhi ata
gur gum gun cha chan
ga gam gan dha dhan don dhut dhuit dhomh dhi
co de cait ciamar carson cuin
mar fhad ge
s dh ag anns san sa
ris leis unnta innte oirre orra rium riut rithe ruinn ruibh
ni mach steach sios suas
gach uile aon da cuid
la latha uair nas
the of and to in for on with as by at from this that
bith bu às den aig tug rinn cuir cur gabh tubhairt tàinig dà far iar""".split())

def process_file(path):
    name = os.path.basename(path)
    if exclude_dwelly and name.startswith("dict_"):
        return None, None
    raw = open(path, encoding="utf-8").read()
    kept = [clean_basic(p) for p in split_paragraphs(raw) if is_gaelic_paragraph(p)]
    if not kept:
        return None, None
    tokens = [w for w in " ".join(kept).split() if looks_real(w)]
    raw_line = " ".join(lemmatize(w) for w in tokens)
    content_line = " ".join(lemmatize(w) for w in tokens if w not in stopwords)
    return raw_line, content_line

raw_lines, content_lines = [], []
for path in glob.glob(os.path.join(input_dir, "*.txt")):
    r, c = process_file(path)
    if r and len(r) > 50:
        raw_lines.append(r)
    if c and len(c.split()) >= 10:
        content_lines.append(c)
open(raw_path, "w", encoding="utf-8").write("\n".join(raw_lines))
open(content_path, "w", encoding="utf-8").write("\n".join(content_lines))
words = open(content_path, encoding="utf-8").read().split()
print(f"Всего документов: {len(content_lines)}, слов: {len(words)}, уникальных: {len(set(words))}")
