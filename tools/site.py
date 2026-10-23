"""Static website: one page per generator with ready-made examples (ru and en), built into docs/ for GitHub Pages.

python3 tools/site.py
"""
import html
import random
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from ideas.tables import GENERATORS, ICONS, make, title_of  # noqa: E402

BASE = "https://savroverside.github.io/ideaforgegen"
OUT = ROOT / "docs"
BOT = "https://t.me/ideaforge_gen_bot"
e = lambda s: html.escape(str(s), quote=True)  # noqa: E731
N = 30

PAGES = {  # kind -> (slug, ru title, ru h1, ru intro, en title, en h1, en intro)
    "npc": ("npc", "Генератор NPC для НРИ: 30 готовых персонажей с секретами", "Генератор персонажей (NPC)",
            "Готовые персонажи для D&amp;D и любой настольной ролевой игры: роль, яркая черта и секрет, который можно раскрыть в нужный момент.",
            "Random NPC Generator: 30 Ready-to-Use Characters with Secrets", "NPC generator",
            "Ready-made characters for D&amp;D and any tabletop RPG: a role, a memorable trait and a secret to reveal at the right moment."),
    "quest": ("quests", "Генератор квестов для НРИ: 30 заданий с подвохом", "Генератор квестов",
              "Задания для игроков: кто заказывает, что нужно сделать, какая награда и где подвох.",
              "Quest Generator: 30 RPG Quests with a Twist", "Quest generator",
              "Jobs for your players: the client, the task, the reward and the twist."),
    "item": ("artifacts", "Генератор магических предметов и артефактов: 30 вещей с ценой", "Генератор артефактов",
             "Странные предметы с силой, ценой за использование и легендой. Подходят для фэнтези, киберпанка и всего между ними.",
             "Magic Item Generator: 30 Artifacts with a Price", "Artifact generator",
             "Strange items with a power, a price for using it and a legend. Fit fantasy, cyberpunk and everything in between."),
    "place": ("locations", "Генератор локаций для НРИ: 30 мест с тайной и опасностью", "Генератор локаций",
              "Места для приключений: атмосфера, тайна и опасность в каждом.",
              "Location Generator: 30 RPG Places with a Secret and a Danger", "Location generator",
              "Places for adventure, each with a mood, a secret and a danger."),
    "faction": ("factions", "Генератор фракций: 30 организаций с целью и лидером", "Генератор фракций",
                "Ордена, синдикаты и культы: чего хотят, как действуют и кто ими правит.",
                "Faction Generator: 30 Organisations with a Goal and a Leader", "Faction generator",
                "Orders, syndicates and cults: what they want, how they act and who leads them."),
    "game": ("game-ideas", "Генератор идей для игр: 30 концептов для разработчиков", "Генератор идей для игр",
             "Жанр, сеттинг, главная механика и поворот: концепты для геймджемов и прототипов.",
             "Game Idea Generator: 30 Concepts for Game Developers", "Game idea generator",
             "Genre, setting, core hook and twist: concepts for game jams and prototypes."),
    "set": ("campaign-kits", "Генератор кампании для НРИ: 30 готовых наборов", "Наборы для кампании",
            "Связанный набор на вечер игры: место, фракция, её лидер и его тайна, задание и награда.",
            "RPG Campaign Generator: 30 Linked Adventure Kits", "Campaign kits",
            "A linked kit for one evening of play: a place, the faction that rules it, its leader and their secret, a job and a prize."),
}

CSS = """
:root{--ink:#191326;--muted:#5a5268;--ground:#f6f4f9;--card:#fff;--line:#e2dcea;--accent:#6a3fc8}
*{box-sizing:border-box}body{margin:0;background:var(--ground);color:var(--ink);font:17px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}
a{color:var(--accent)}.wrap{max-width:900px;margin:0 auto;padding:0 20px}
header{background:var(--card);border-bottom:1px solid var(--line)}header .wrap{display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:60px;flex-wrap:wrap}
.brand{font-weight:800;text-decoration:none;color:var(--ink);font-size:19px}nav a{margin-left:12px}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:0 18px;border-radius:12px;background:var(--accent);color:#fff;font-weight:700;text-decoration:none}
h1{font-size:clamp(28px,5vw,40px);line-height:1.15;margin:32px 0 8px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px;padding:0;list-style:none}
.cards li{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px}
.cards b{display:block;margin-bottom:6px}.cards dl{margin:0}.cards dt{font-weight:700;color:var(--accent);font-size:14px}.cards dd{margin:0 0 6px}
.cta{background:var(--ink);color:#fff;border-radius:18px;padding:24px;margin:28px 0;display:flex;flex-wrap:wrap;gap:16px;align-items:center;justify-content:space-between}
.cta p{margin:0;flex:1 1 320px}.cta .btn{background:#fff;color:var(--ink)}
.gens{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px;padding:0;list-style:none}
.gens a{display:block;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;text-decoration:none;color:var(--ink);font-weight:700}
footer{color:var(--muted);font-size:14px;padding:32px 0 48px}
"""


def page(lang, path, title, desc, body, alt_path):
    depth = "../" * path.count("/")
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><meta name="description" content="{desc}">
<link rel="canonical" href="{BASE}/{path}">
<link rel="alternate" hreflang="{'en' if lang == 'ru' else 'ru'}" href="{BASE}/{alt_path}">
<meta property="og:title" content="{title}"><meta property="og:description" content="{desc}"><meta property="og:image" content="{BASE}/og.jpg">
<link rel="stylesheet" href="{depth}style.css">
</head>
<body>
<header><div class="wrap"><a class="brand" href="{depth}{'' if lang == 'ru' else 'en/'}">IdeaForge</a>
<nav><a href="{depth}{alt_path}">{'English' if lang == 'ru' else 'Русский'}</a> <a class="btn" href="{BOT}">{'Генерировать в Telegram' if lang == 'ru' else 'Generate in Telegram'}</a></nav></div></header>
<main class="wrap">{body}</main>
<footer class="wrap">{'IdeaForge: генератор идей для игр и НРИ. Каждый вечер новая идея в канале' if lang == 'ru' else 'IdeaForge: an idea generator for games and tabletop RPGs. A new idea every evening in'} <a href="https://t.me/ideaforges">@ideaforges</a>. {'Ещё наш проект' if lang == 'ru' else 'Also by us'}: <a href="https://savroverside.github.io/wordlore/">{'истории происхождения слов' if lang == 'ru' else 'the stories behind words (in Russian)'}</a>.</footer>
</body></html>
"""


def cards(kind, lang, seed):
    rnd = random.Random(seed)
    i = 0 if lang == "ru" else 1
    out, seen = [], set()
    while len(out) < N:
        idea = make(kind, rnd.getrandbits(32))
        key = tuple(v[i] for _, v in idea["rows"])
        if key in seen:
            continue
        seen.add(key)
        rows = "".join(f"<dt>{e(lab[i])}</dt><dd>{e(val[i][:1].upper() + val[i][1:])}</dd>" for lab, val in idea["rows"])
        out.append(f"<li><b>{ICONS[kind]} {e(title_of(idea, i))}</b><dl>{rows}</dl></li>")
    return "".join(out)


def main():
    (OUT / "en").mkdir(parents=True, exist_ok=True)
    (OUT / "style.css").write_text(CSS.strip() + "\n", encoding="utf-8")
    urls = []
    for lang in ("ru", "en"):
        pre = "" if lang == "ru" else "en/"
        other = "en/" if lang == "ru" else ""
        links = []
        for n, (kind, (slug, rt, rh, ri, et, eh, ei)) in enumerate(PAGES.items()):
            title, h1, intro = (rt, rh, ri) if lang == "ru" else (et, eh, ei)
            cta = ("<b>Нужно ещё?</b> В боте 5 новых карточек каждый день бесплатно, с картинкой, избранным и наборами для кампании."
                   if lang == "ru" else "<b>Need more?</b> The bot gives 5 new cards a day for free, with pictures, favourites and campaign kits.")
            body = (f"<p><a href=\"./\">{'← Все генераторы' if lang == 'ru' else '← All generators'}</a></p><h1>{h1}</h1><p>{intro}</p>"
                    f"<ul class=\"cards\">{cards(kind, lang, 1000 + n)}</ul>"
                    f"<div class=\"cta\"><p>{cta}</p><a class=\"btn\" href=\"{BOT}\">{'Открыть бота' if lang == 'ru' else 'Open the bot'}</a></div>")
            (OUT / pre / f"{slug}.html").write_text(page(lang, f"{pre}{slug}.html", title, intro, body, f"{other}{slug}.html"), encoding="utf-8")
            urls.append(f"{BASE}/{pre}{slug}.html")
            links.append(f'<li><a href="{slug}.html">{ICONS[kind]} {h1}</a></li>')
        if lang == "ru":
            body = ("<h1>Генераторы идей для игр и НРИ</h1><p>Персонажи, квесты, артефакты, локации, фракции, идеи игр и готовые наборы для кампании. "
                    "На каждой странице 30 готовых примеров, бери и используй в своей игре.</p>"
                    f"<ul class=\"gens\">{''.join(links)}</ul>"
                    "<div class=\"cta\"><p><b>Книга «Степь и статика»:</b> 100 странных идей для любой НРИ одним PDF, с таблицами для бросков d20.</p>"
                    f"<a class=\"btn\" href=\"{BOT}?start=book\">Посмотреть книгу</a></div>")
            title, desc = "Генераторы идей для НРИ и игр: NPC, квесты, артефакты, локации", "Готовые идеи для настольных ролевых игр и разработчиков игр: персонажи, квесты, артефакты, локации, фракции."
        else:
            body = ("<h1>Idea generators for games and tabletop RPGs</h1><p>Characters, quests, artifacts, locations, factions, game ideas and ready-made campaign kits. "
                    "Every page has 30 ready examples to use in your game.</p>"
                    f"<ul class=\"gens\">{''.join(links)}</ul>"
                    "<div class=\"cta\"><p><b>The book Steppe &amp; Static:</b> 100 weird seeds for any RPG in one PDF, with d20 roll tables.</p>"
                    f"<a class=\"btn\" href=\"{BOT}?start=book\">See the book</a></div>")
            title, desc = "RPG Idea Generators: NPCs, Quests, Magic Items, Locations", "Ready-made ideas for tabletop RPGs and game developers: characters, quests, artifacts, locations and factions."
        (OUT / pre / "index.html").write_text(page(lang, f"{pre}index.html" if pre else "", title, desc, body, f"{other}index.html" if other else ""), encoding="utf-8")
        urls.append(f"{BASE}/{pre}")
    today = date.today().isoformat()
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                     + "".join(f"<url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print(len(urls), "pages")


if __name__ == "__main__":
    main()
