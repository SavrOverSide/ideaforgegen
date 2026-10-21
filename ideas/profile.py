"""What people see before they press START, and the command menu."""
COMMANDS = {
    "ru": [("start", "Начать"), ("game", "Идея игры"), ("npc", "Персонаж"), ("faction", "Фракция"), ("item", "Артефакт"),
           ("quest", "Квест"), ("place", "Локация"), ("set", "Набор для кампании"), ("book", "Книга: 100 идей для НРИ"), ("deck", "PDF-колода для печати"), ("saved", "Избранное"), ("invite", "Позвать друга, получить генерации"),
           ("sub", "Идея дня в личку: вкл/выкл"), ("buy", "Баланс и покупки"), ("lang", "English / Русский")],
    "en": [("start", "Start"), ("game", "Game idea"), ("npc", "Character"), ("faction", "Faction"), ("item", "Artifact"),
           ("quest", "Quest"), ("place", "Location"), ("set", "Campaign kit"), ("book", "Book: 100 RPG seeds"), ("deck", "Printable PDF deck"), ("saved", "Saved ideas"), ("invite", "Invite a friend, get generations"),
           ("sub", "Daily idea in DM: on/off"), ("buy", "Balance and purchases"), ("lang", "English / Русский")],
}
DESCRIPTION = {
    "ru": ("Застрял с идеей для игры или кампании? Нажми кнопку и получи готовую карточку: идею игры, персонажа с секретом, "
           "фракцию, артефакт, квест или локацию.\n\nПодходит разработчикам игр и мастерам настольных ролёвок. "
           "5 карточек в день бесплатно, лучшие можно сохранить.\n\nНажми START."),
    "en": ("Stuck for a game or campaign idea? Tap a button and get a finished card: a game concept, a character with a secret, "
           "a faction, an artifact, a quest or a location.\n\nBuilt for game developers and tabletop GMs. "
           "5 cards a day are free, and you can save the best ones.\n\nPress START."),
}
SHORT = {
    "ru": "Идеи для игр и НРИ: персонажи, фракции, артефакты, квесты",
    "en": "Ideas for games and tabletop RPGs: characters, factions, artifacts, quests",
}
