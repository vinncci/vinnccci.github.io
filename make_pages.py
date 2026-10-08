import html, json, pathlib, re, sys, unicodedata, urllib.parse, urllib.request

DOMAIN = "https://jerkmate.lol"
FOLDER = "track"

# --- Look of the embed (edit these) ---
THEME_COLOR = "#010101"
SITE_NAME = ""              # e.g. "v1nc1" for small text above the title; "" to hide
IMAGE = "cover"             # "cover" = the song's Spotify cover, or a repo path like "images/merica.jpg"
FALLBACK_ARTIST = "v1nc1"   # used if the artist can't be found; "" for no fallback
DESCRIPTION_FORMAT = "{artist}"   # the small text under the title, e.g. "by {artist}"

def meta(prop, content, attr="property"):
    return f'<meta {attr}="{prop}" content="{html.escape(content, quote=True)}" />'

def render(title, description, image, page_url, target):
    tags = [
        meta("og:type", "website"),
        meta("og:title", title),
        meta("og:url", page_url),
        meta("og:image", image),
        meta("twitter:card", "summary_large_image", attr="name"),
        meta("theme-color", THEME_COLOR, attr="name"),
    ]
    if SITE_NAME:
        tags.append(meta("og:site_name", SITE_NAME))
    if description:
        tags.append(meta("og:description", description))
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8" />\n'
        f"<title>{html.escape(title)}</title>\n"
        + "\n".join(tags)
        + f"\n<script>location.replace({json.dumps(target)});</script>\n"
        "</head>\n"
        f'<body><a href="{html.escape(target)}">Open in Spotify</a></body>\n</html>\n'
    )

def parse(link):
    m = re.search(r"open\.spotify\.com/(?:intl-[a-z]+/)?(track|album|artist|playlist)/([A-Za-z0-9]+)", link)
    if not m:
        raise ValueError(f"Not a Spotify link: {link}")
    return m.group(1), m.group(2)

def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text[:60].strip("-")

def get_artist(target, kind):
    """Try to read the artist from the Spotify page's og:description."""
    if kind not in ("track", "album"):
        return ""
    try:
        req = urllib.request.Request(
            target, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en"})
        page = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "ignore")
        tag = re.search(r'<meta[^>]*og:description[^>]*>', page)
        if not tag:
            return ""
        content = re.search(r'content="([^"]*)"', tag.group(0))
        if not content:
            return ""
        desc = html.unescape(content.group(1))
        desc = re.sub(r"^Listen to .*? on Spotify\.\s*", "", desc)
        first = desc.split(" · ")[0].strip()
        return first if 0 < len(first) <= 80 else ""
    except Exception:
        return ""

def to_bold(text):
    out = []
    for ch in text:
        if "A" <= ch <= "Z":
            out.append(chr(0x1D5D4 + ord(ch) - ord("A")))
        elif "a" <= ch <= "z":
            out.append(chr(0x1D5EE + ord(ch) - ord("a")))
        elif "0" <= ch <= "9":
            out.append(chr(0x1D7EC + ord(ch) - ord("0")))
        else:
            out.append(ch)
    return "".join(out)

def build(link):
    kind, sid = parse(link)
    target = f"https://open.spotify.com/{kind}/{sid}"
    api = "https://open.spotify.com/oembed?url=" + urllib.parse.quote(target, safe="")
    with urllib.request.urlopen(api, timeout=15) as r:
        data = json.load(r)

    song = data["title"]
    artist = get_artist(target, kind)
    source = "found"
    if not artist:
        artist = FALLBACK_ARTIST
        source = "fallback"
    description = DESCRIPTION_FORMAT.format(artist=to_bold(artist)) if artist else ""

    slug = slugify(song) or sid
    folder = pathlib.Path(FOLDER) / slug
    page = folder / "index.html"
    if page.exists() and target not in page.read_text(encoding="utf-8"):
        slug = f"{slug}-{sid[:6].lower()}"
        folder = pathlib.Path("t") / slug
        page = folder / "index.html"

    folder.mkdir(parents=True, exist_ok=True)
    page_url = f"{DOMAIN}/{FOLDER}/{slug}/"
    image = data["thumbnail_url"] if IMAGE == "cover" else f"{DOMAIN}/{IMAGE.lstrip('/')}"
    page.write_text(render(song, description, image, page_url, target), encoding="utf-8")
    print(f"{song} | {description}  [artist {source}]  ->  {page_url}")

links = sys.argv[1:]
if not links:
    p = pathlib.Path("links.txt")
    if p.exists():
        links = [l.strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    else:
        print("links.txt not found in", pathlib.Path.cwd())

print(f"Found {len(links)} link(s)")

for link in links:
    try:
        build(link)
    except Exception as e:
        print(f"FAILED {link}: {e}")
