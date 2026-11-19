from __future__ import annotations

from typing import Sequence
from .combat import BattleEvent, BattleReport, EventType, Outcome, Participant, Side
from .hero import Hero
from .items import CHAINMAIL, ELVEN_BOW, EMBER_STAFF, IRON_SWORD, Item, ItemCatalog, PLATE_ARMOR, create_default_catalog
from .kits import HeroClass
from .world import Crypt, DragonLair, ExpeditionReport, Forest, HauntedMansion, LocationRegistry, Merchant, Rewards
from .patterns import GameFacade, JsonSave, CachedSave, Balanced, Aggressive, Cautious


# весь вывод в консоль собран здесь
class ConsoleView:

    def describe(self, item: Item) -> str:
        description = item.name

        if item.enchantments:
            names = []
            for enchantment in item.enchantments:
                names.append(enchantment.name)
            description += " [" + ", ".join(names) + "]"

        return description + " (" + item.description + ")"

    def print_hero(self, hero: Hero) -> None:
        print(
            f"{hero.name}, {hero.hero_class.display_name} {hero.level} ур. | здоровье {hero.max_health} | "
            f"опыт {hero.experience}/{hero.experience_to_next_level} | золото {hero.gold}"
        )
        print("  Оружие: " + self.describe(hero.weapon))
        print("  Броня:  " + self.describe(hero.armor))

    def print_report(self, report: ExpeditionReport, location_name: str) -> None:
        battle = report.battle
        print(f"=== {location_name} (сид {report.seed}) ===")
        print(f"{battle.hero.name} встречает врага: {battle.enemy.name} ({battle.enemy.max_health} здоровья)")

        for event in battle.events:
            self._print_event(event, battle)

        self._print_rewards(battle, report.rewards)

    def _print_event(self, event: BattleEvent, battle: BattleReport) -> None:
        source = self._participant(event.source, battle)
        target = self._participant(event.target, battle)

        if event.type == EventType.HIT:
            print(
                f"[раунд {event.round}] {source.name} -> {target.name}: {event.amount} урона, "
                f"осталось {event.target_health_after}/{target.max_health}"
            )
        elif event.type == EventType.CRITICAL_HIT:
            print(
                f"[раунд {event.round}] {source.name} -> {target.name}: КРИТ! {event.amount} урона, "
                f"осталось {event.target_health_after}/{target.max_health}"
            )
        elif event.type == EventType.DEATH:
            print(f"{target.name} повержен!")

    def _print_rewards(self, battle: BattleReport, rewards: Rewards) -> None:
        if battle.outcome == Outcome.DEFEAT:
            print(f"Поражение... {battle.hero.name} едва уносит ноги и теряет {-rewards.gold} золота")
            return

        print(f"Победа! +{rewards.experience} опыта, +{rewards.gold} золота")
        if rewards.loot is not None:
            print("Добыча: " + self.describe(rewards.loot))
        if rewards.levels_gained > 0:
            print("Новый уровень!")

    def _participant(self, side: Side, battle: BattleReport) -> Participant:
        return battle.hero if side == Side.HERO else battle.enemy


VIEW = ConsoleView()


def main() -> None:
    catalog = create_default_catalog()
    locations = LocationRegistry([
        Forest(catalog),
        Crypt(catalog),
        DragonLair(catalog),
        HauntedMansion(catalog),
    ])
    merchant = Merchant(catalog, [
        IRON_SWORD, ELVEN_BOW, EMBER_STAFF, CHAINMAIL, PLATE_ARMOR,
    ])

    game = GameFacade(locations, CachedSave(JsonSave("save.json", catalog)))
    hero = create_hero(catalog)
    print(f"{hero.name} разбивает лагерь на опушке мистического леса.")

    while True:
        print()
        VIEW.print_hero(hero)
        print("1 - экспедиция, 2 - снаряжение, 3 - торговец, 4 - сохранить, 5 - загрузить, 6 - достижения и журнал, 0 - выход")
        choice = input().strip()
        if choice == "1":
            go_on_expedition(hero, locations, game)
        elif choice == "2":
            manage_equipment(hero)
        elif choice == "3":
            visit_merchant(hero, merchant)
        elif choice == "4":
            try:
                game.save(hero)
                print("Игра сохранена в save.json")
            except OSError as error:
                print(f"Ошибка сохранения: {error}")
        elif choice == "5":
            try:
                hero = game.load()
                print("Игра загружена")
            except (OSError, ValueError, KeyError, StopIteration) as error:
                print(f"Ошибка загрузки: {error}")
        elif choice == "6":
            print("Достижения: " + (", ".join(hero.achievements) or "пока нет"))
            print("Журнал экспедиций:")
            print("\n".join(game.journal.entries) or "пока пуст")
        elif choice == "0":
            return
        else:
            print("Такого варианта нет")


def create_hero(catalog: ItemCatalog) -> Hero:
    print("Создайте своего героя!")
    while True:
        print("Выберите класс:")
        hero_classes = list(HeroClass)
        for i, hero_class in enumerate(hero_classes):
            kit = hero_class.starter_kit(catalog)
            print(
                f"{i + 1} - {hero_class.display_name} (здоровье {hero_class.base_health}): "
                f"{VIEW.describe(kit.create_weapon())}, {VIEW.describe(kit.create_armor())}"
            )
        class_index = read_choice(len(hero_classes))
        if class_index < 0:
            continue
        hero_class = hero_classes[class_index]

        print("Введите имя:")
        name = input().strip()

        try:
            return (
                Hero.Builder()
                .set_name(name)
                .set_hero_class(hero_class)
                .set_starter_kit(hero_class.starter_kit(catalog))
                .build()
            )
        except ValueError as error:
            print(f"Не получилось создать героя: {error}")


def go_on_expedition(hero: Hero, locations: LocationRegistry, game: GameFacade) -> None:
    all_locations = locations.all
    print("Куда отправимся?")
    for i, location in enumerate(all_locations):
        print(f"{i + 1} - {location.display_name} (рекомендуемый уровень {location.recommended_level})")
    index = read_choice(len(all_locations))
    if index < 0:
        return

    location = all_locations[index]
    print("Выберите стратегию: 1 - обычная, 2 - агрессивная, 3 - осторожная")
    strategy_index = read_choice(3)
    if strategy_index < 0:
        return
    strategy = (Balanced, Aggressive, Cautious)[strategy_index]()
    report = game.explore(hero, location, strategy)
    print()
    VIEW.print_report(report, location.display_name)

    if report.battle.outcome == Outcome.VICTORY and location.code == DragonLair.CODE:
        print(f"\nДракон повержен! Барды еще долго будут петь о подвиге героя по имени {hero.name}.")


def manage_equipment(hero: Hero) -> None:
    inventory = hero.inventory
    if not inventory:
        print("Инвентарь пуст")
        return

    print("Что экипировать? (0 - назад)")
    print_items(inventory)
    index = read_choice(len(inventory))
    if index < 0:
        return

    item = inventory[index]
    hero.equip(item)
    print("Экипировано: " + VIEW.describe(item))


def visit_merchant(hero: Hero, merchant: Merchant) -> None:
    print(f'Торговец: "Чего желаешь?" (золото: {hero.gold})')
    print("1 - купить, 2 - продать, 0 - назад")
    choice = input().strip()
    if choice == "1":
        buy(hero, merchant)
    elif choice == "2":
        sell(hero, merchant)


def buy(hero: Hero, merchant: Merchant) -> None:
    showcase = merchant.showcase
    for i, item in enumerate(showcase):
        print(f"{i + 1} - {VIEW.describe(item)}: {item.price} золота")
    index = read_choice(len(showcase))
    if index < 0:
        return

    try:
        item = merchant.buy(hero, showcase[index].code)
        print("Куплено: " + VIEW.describe(item))
    except ValueError as error:
        print(error)


def sell(hero: Hero, merchant: Merchant) -> None:
    inventory = hero.inventory
    if not inventory:
        print("Продавать нечего (экипированные предметы продать нельзя)")
        return

    for i, item in enumerate(inventory):
        print(f"{i + 1} - {VIEW.describe(item)}: {merchant.sell_price(item)} золота")
    index = read_choice(len(inventory))
    if index < 0:
        return

    item = inventory[index]
    price = merchant.sell(hero, item)
    print(f"Продано: {item.name} за {price} золота")


def print_items(items: Sequence[Item]) -> None:
    for i, item in enumerate(items):
        print(f"{i + 1} - {VIEW.describe(item)}")


# читает номер варианта от 1 до count, возвращает индекс или -1, если ввели что-то другое
def read_choice(count: int) -> int:
    try:
        choice = int(input().strip())
        if 1 <= choice <= count:
            return choice - 1
    except ValueError:
        # некорректный ввод обрабатываем так же, как отказ от выбора
        pass

    return -1


if __name__ == "__main__":
    main()
