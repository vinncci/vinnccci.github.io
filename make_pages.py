import html, json, pathlib, re, sys, urllib.parse, urllib.request

DOMAIN = "https://jerkmate.lol"

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>{title}</title>
<meta property="og:type" content="website" />
<meta property="og:site_name" content="Spotify" />
<meta property="og:title" content="{title}" />
<meta property="og:description" content="Listen on Spotify" />
<meta property="og:image" content="{image}" />
<meta property="og:url" content="{page_url}" />
<meta name="twitter:card" content="summary" />
<meta name="theme-color" content="#1DB954" />
<script>location.replace({target_js});</script>
</head>
<body><a href="{target}">Open in Spotify</a></body>
</html>
"""

def parse(link):
    m = re.search(r"open\.spotify\.com/(?:intl-[a-z]+/)?(track|album|artist|playlist)/([A-Za-z0-9]+)", link)
    if not m:
        raise ValueError(f"Not a Spotify link: {link}")
    return m.group(1), m.group(2)

def build(link):
    kind, sid = parse(link)
    target = f"https://open.spotify.com/{kind}/{sid}"
    api = "https://open.spotify.com/oembed?url=" + urllib.parse.quote(target, safe="")
    with urllib.request.urlopen(api, timeout=15) as r:
        data = json.load(r)
    out = pathlib.Path("t") / sid
    out.mkdir(parents=True, exist_ok=True)
    page_url = f"{DOMAIN}/t/{sid}/"
    (out / "index.html").write_text(TEMPLATE.format(
        title=html.escape(data["title"]),
        image=html.escape(data["thumbnail_url"]),
        page_url=page_url,
        target=target,
        target_js=json.dumps(target),
    ), encoding="utf-8")
    print(f"{data['title']}  ->  {page_url}")

for link in sys.argv[1:]:
    try:
        build(link)
    except Exception as e:
        print(f"FAILED {link}: {e}")
