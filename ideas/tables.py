"""Generation tables. Each entry is (ru, en)."""
import random

GENRE = [("рогалик", "roguelike"), ("метроидвания", "metroidvania"), ("иммерсив-сим", "immersive sim"),
         ("карточная стратегия", "deckbuilder"), ("симулятор выживания", "survival sim"),
         ("детектив", "detective game"), ("тактическая RPG", "tactics RPG"), ("ритм-игра", "rhythm game"),
         ("градостроитель", "city builder"), ("файтинг", "fighting game"), ("хоррор", "horror game"),
         ("уютный симулятор", "cozy sim")]
SETTING = [("затонувший мегаполис", "a sunken megacity"), ("кочевой город на спине гигантского зверя", "a nomad city on a giant beast's back"),
           ("последний поезд в вечной зиме", "the last train in an endless winter"), ("монастырь хакеров в горах", "a mountain monastery of hackers"),
           ("степь после падения орбитальной станции", "a steppe after an orbital station crash"), ("сон умирающего бога", "a dying god's dream"),
           ("киберпанк-базар в Алматы 2099", "a cyberpunk bazaar in Almaty, 2099"), ("архипелаг, где острова перемещаются", "an archipelago of drifting islands"),
           ("подпольная бойцовская лига роботов", "an underground robot fight league"), ("библиотека, в которой слова живые", "a library where words are alive"),
           ("колония на комете", "a colony on a comet"), ("панельный район, застрявший во времени", "a block of flats stuck in time")]
MECHANIC = [("время идёт, только когда ты двигаешься", "time moves only when you move"), ("ты играешь за двух персонажей одновременно", "you control two characters at once"),
            ("каждая смерть меняет карту навсегда", "every death permanently changes the map"), ("язык врагов нужно расшифровать", "you must decipher the enemies' language"),
            ("оружие собирается из слов", "weapons are crafted from words"), ("звук виден и опасен", "sound is visible and dangerous"),
            ("мир меняется от твоей музыки", "the world reacts to your music"), ("ресурсом служат воспоминания", "memories are the currency"),
            ("свет и тень меняются местами", "light and shadow swap places"), ("NPC запоминают всё и сплетничают", "NPCs remember everything and gossip")]
TWIST = [("главный враг это будущий ты", "the main villain is your future self"), ("туториал врёт", "the tutorial is lying"),
         ("игрок на самом деле босс чужой игры", "you are the boss of someone else's game"), ("мир это симуляция для обучения ИИ", "the world is an AI training simulation"),
         ("спасать нужно не принцессу, а злодея", "you must save the villain, not the princess"), ("карта это тело существа", "the map is a living creature's body")]

ROLE = [("наёмница", "mercenary"), ("алхимик", "alchemist"), ("бродячий философ", "wandering philosopher"),
        ("бывший чемпион по боям без правил", "ex-MMA champion"), ("хакер-отшельник", "hermit hacker"), ("переводчик мёртвых языков", "translator of dead languages"),
        ("контрабандист", "smuggler"), ("шаман-инженер", "shaman engineer"), ("уличный музыкант", "street musician"), ("картограф", "cartographer")]
TRAIT = [("говорит только загадками", "speaks only in riddles"), ("никогда не лжёт, но всегда недоговаривает", "never lies, but never tells everything"),
         ("коллекционирует чужие имена", "collects other people's names"), ("боится тишины", "is afraid of silence"),
         ("смеётся в самые страшные моменты", "laughs at the worst moments"), ("цитирует стоиков", "quotes the Stoics"),
         ("помнит прошлые жизни, но путает их", "remembers past lives but mixes them up")]
SECRET = [("работает на тех, с кем борется", "works for the people they fight"), ("уже умер однажды", "has died once already"),
          ("украл чужое лицо", "stole someone's face"), ("знает, как закончится мир", "knows how the world ends"),
          ("на самом деле ребёнок в теле взрослого", "is a child in an adult's body"), ("должен огромный долг духу", "owes a huge debt to a spirit")]

GOAL = [("вернуть забытый язык", "revive a forgotten language"), ("остановить время в одном городе", "freeze time in one city"),
        ("загрузить сознания людей в машину", "upload human minds into a machine"), ("уничтожить все карты мира", "destroy every map in the world"),
        ("доказать, что богов не существует", "prove the gods do not exist"), ("собрать армию из снов", "raise an army of dreams")]
METHOD = [("через музыку и подпольные концерты", "through music and underground gigs"), ("подкупом и шантажом", "by bribery and blackmail"),
          ("проповедью нонконформизма", "by preaching nonconformity"), ("турнирами единоборств", "through martial arts tournaments"),
          ("взламывая городские системы", "by hacking city systems"), ("торгуя запретными знаниями", "by trading forbidden knowledge")]
FACTION_WORD = [("Орден", "Order"), ("Братство", "Brotherhood"), ("Синдикат", "Syndicate"), ("Ковен", "Coven"), ("Лига", "League"), ("Коллектив", "Collective")]
FACTION_OF = [("Серого Ветра", "of the Grey Wind"), ("Тихих Струн", "of Silent Strings"), ("Последнего Слова", "of the Last Word"),
              ("Ржавой Луны", "of the Rusted Moon"), ("Пустого Трона", "of the Empty Throne"), ("Стеклянной Степи", "of the Glass Steppe")]

SYL = ["ka", "ra", "zu", "mir", "tal", "en", "or", "vy", "sha", "lek", "dar", "ni", "bo", "rus", "an", "el", "kai", "tor", "yul", "ix",
       "sa", "ta", "mu", "bek", "gul", "nur", "ai", "dos", "ar", "say", "tem", "oy", "zhan", "kor", "ul", "ba", "lun", "mar", "vei", "dro"]

from .tables_extra import EXTRA  # noqa: E402

for _name, _table in (("GENRE", GENRE), ("SETTING", SETTING), ("MECHANIC", MECHANIC), ("TWIST", TWIST), ("ROLE", ROLE), ("TRAIT", TRAIT),
                      ("SECRET", SECRET), ("GOAL", GOAL), ("METHOD", METHOD), ("FACTION_WORD", FACTION_WORD), ("FACTION_OF", FACTION_OF)):
    _table.extend(tuple(e) for e in EXTRA[_name])



def name() -> str:
    return "".join(random.choice(SYL) for _ in range(random.randint(2, 3))).capitalize()


def pick(table):
    return random.choice(table)


# Each generator returns ONE idea: a name and rows of (label, value-ru, value-en). The same idea
# is then shown in either language (and in the channel post in both), so ru and en always match.
def game() -> dict:
    return {"kind": "game", "name": name(), "rows": [
        (("Жанр", "Genre"), pick(GENRE)), (("Сеттинг", "Setting"), pick(SETTING)),
        (("Фишка", "Hook"), pick(MECHANIC)), (("Поворот", "Twist"), pick(TWIST))]}


def npc() -> dict:
    return {"kind": "npc", "name": name(), "rows": [
        (("Роль", "Role"), pick(ROLE)), (("Черта", "Trait"), pick(TRAIT)), (("Секрет", "Secret"), pick(SECRET))]}


def faction() -> dict:
    word, of, leader = pick(FACTION_WORD), pick(FACTION_OF), name()
    return {"kind": "faction", "name": f"{word[0]} {of[0]}", "name_en": f"{word[1]} {of[1]}", "rows": [
        (("Цель", "Goal"), pick(GOAL)), (("Метод", "Method"), pick(METHOD)), (("Лидер", "Leader"), (leader, leader))]}


import json  # noqa: E402
from pathlib import Path  # noqa: E402

K = {k: [tuple(e) for e in v] for k, v in json.loads((Path(__file__).parent / "kinds.json").read_text("utf-8")).items()}


def item() -> dict:
    return {"kind": "item", "name": name(), "rows": [
        (("Предмет", "Item"), pick(K["ITEM_TYPE"])), (("Сила", "Power"), pick(K["ITEM_POWER"])),
        (("Цена", "Cost"), pick(K["ITEM_COST"])), (("Легенда", "Lore"), pick(K["ITEM_LORE"]))]}


def quest() -> dict:
    return {"kind": "quest", "name": name(), "rows": [
        (("Заказчик", "Client"), pick(K["QUEST_CLIENT"])), (("Задание", "Task"), pick(K["QUEST_TASK"])),
        (("Награда", "Reward"), pick(K["QUEST_REWARD"])), (("Поворот", "Twist"), pick(K["QUEST_TWIST"]))]}


def place() -> dict:
    return {"kind": "place", "name": name(), "rows": [
        (("Место", "Place"), pick(K["PLACE_TYPE"])), (("Атмосфера", "Mood"), pick(K["PLACE_MOOD"])),
        (("Тайна", "Secret"), pick(K["PLACE_SECRET"])), (("Опасность", "Danger"), pick(K["PLACE_DANGER"]))]}


GENERATORS = {"game": game, "npc": npc, "faction": faction, "item": item, "quest": quest, "place": place}
ICONS = {"game": "🎮", "npc": "🧙", "faction": "⚔️", "item": "🗡️", "quest": "📜", "place": "🏰"}
KIND_TITLE = {"game": ("ИДЕЯ ИГРЫ", "GAME IDEA"), "npc": ("ПЕРСОНАЖ", "CHARACTER"), "faction": ("ФРАКЦИЯ", "FACTION"),
              "item": ("АРТЕФАКТ", "ARTIFACT"), "quest": ("КВЕСТ", "QUEST"), "place": ("ЛОКАЦИЯ", "LOCATION")}


def make(kind: str, seed: int = None):
    """Builds an idea. The same (kind, seed) always gives the same idea, so a saved idea is just its seed."""
    if seed is None:
        seed = random.getrandbits(32)
    state = random.getstate()
    random.seed(seed)
    try:
        idea = GENERATORS[kind]()
    finally:
        random.setstate(state)
    idea["seed"] = seed
    return idea


def title_of(idea: dict, i: int) -> str:
    return idea["name_en"] if i == 1 and "name_en" in idea else idea["name"]


def text(idea: dict, lang: str) -> str:
    """Caption / plain-text form of an idea in one language."""
    i = 0 if lang == "ru" else 1
    lines = [f"{ICONS[idea['kind']]} <b>{title_of(idea, i)}</b>"]
    lines += [f"{label[i]}: {value[i]}" for label, value in idea["rows"]]
    return "\n".join(lines)


def text_both(idea: dict) -> str:
    return f"{text(idea, 'ru')}\n\n—\n\n{text(idea, 'en')}"
