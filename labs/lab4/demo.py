from __future__ import annotations

from .dice import Dice
from .hero import Hero
from .items import FIERY, IRON_SWORD, create_default_catalog
from .kits import HeroClass
from .main import ConsoleView
from .world import Crypt, Forest


def main() -> None:
    catalog = create_default_catalog()
    view = ConsoleView()

    print("===== Одиночка =====")
    first = Dice()
    second = Dice()
    print(f"Dice() возвращает один и тот же объект: {first is second}")

    print()
    print("===== Прототип =====")
    plain_sword = catalog.create(IRON_SWORD)
    fiery_sword = catalog.create(IRON_SWORD)
    fiery_sword.enchant(FIERY)
    print("Первая копия:        " + view.describe(plain_sword))
    print("Вторая копия:        " + view.describe(fiery_sword))
    print("Новая копия шаблона: " + view.describe(catalog.create(IRON_SWORD)))
    print(f"Копии - разные объекты: {plain_sword is not fiery_sword}")

    print()
    print("===== Абстрактная фабрика =====")
    for hero_class in HeroClass:
        kit = hero_class.starter_kit(catalog)
        print(
            f"{hero_class.display_name}: {view.describe(kit.create_weapon())}, "
            f"{view.describe(kit.create_armor())}"
        )

    print()
    print("===== Строитель =====")
    hero = (
        Hero.Builder()
        .set_name("Артур")
        .set_hero_class(HeroClass.WARRIOR)
        .set_starter_kit(HeroClass.WARRIOR.starter_kit(catalog))
        .set_level(3)
        .build()
    )
    view.print_hero(hero)
    try:
        (
            Hero.Builder()
            .set_hero_class(HeroClass.MAGE)
            .set_starter_kit(HeroClass.MAGE.starter_kit(catalog))
            .build()
        )
    except ValueError as error:
        print(f"Герой без имени не создается: {error}")
    try:
        Hero.Builder().set_name("Мерлин").build()
    except ValueError as error:
        print(f"Герой без класса не создается: {error}")

    print()
    print("===== Фабричный метод =====")
    forest = Forest(catalog)
    crypt = Crypt(catalog)
    view.print_report(forest.explore(hero, 7), forest.display_name)
    print()
    view.print_report(crypt.explore(hero, 7), crypt.display_name)

    from tempfile import TemporaryDirectory
    from pathlib import Path
    from .patterns import (Aggressive, Balanced, Cautious, CachedSave, Damage,
                           DoubleAttackEnemy, GameFacade, JsonSave, Shield,
                           StrongEnemy, ArmoredEnemy)
    from .enemies import Goblin
    from .world import HauntedMansion, LocationRegistry

    print("\n===== Паттерны лабораторной 4 =====")
    enemy = ArmoredEnemy(DoubleAttackEnemy(StrongEnemy(Goblin())))
    print("Декоратор:", enemy.name, "урон:", enemy.roll_damage().damage)
    mansion = HauntedMansion(catalog)
    print("Адаптер:", mansion._create_enemy().name)
    print("Стратегии:", *(f"{t.__name__}: атака {t.attack_factor}, защита {t.defense_factor}"
                          for t in (Balanced, Aggressive, Cautious)), sep="\n")
    damage = Shield(3, Shield(2)).apply(Damage(10))
    print(f"Цепочка защиты: поглощено {damage.absorbed}, прошло {damage.amount}")
    with TemporaryDirectory() as directory:
        storage = CachedSave(JsonSave(Path(directory) / "hero.json", catalog))
        game = GameFacade(LocationRegistry([mansion]), storage)
        report = game.explore(hero, mansion, Balanced(), 42)
        print("Фасад и наблюдатели:", report.battle.outcome.value, game.journal.entries)
        print("Достижения:", hero.achievements)
        game.save(hero)
        restored = game.load()
        print("Заместитель и сохранение:", restored.name, restored.level, restored.gold)


if __name__ == "__main__":
    main()
