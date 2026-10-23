from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable
from .combat import Battle, BattleReport, Outcome
from .dice import Dice, UnknownCodeError
from .enemies import Dragon, Enemy, Goblin, Skeleton
from .hero import Hero
from .items import BONE_BOW, CRYPT_MAIL, DAWN_BLADE, DRAGONSCALE_ARMOR, GOBLIN_CLEAVER, HUNTING_BOW, Item, ItemCatalog, KNIGHT_BLADE, LEATHER_ARMOR, NECROMANCER_STAFF


# итоги экспедиции для героя;
# gold отрицательный, если герой проиграл и потерял золото, loot равен None, если добычи нет
@dataclass(frozen=True)
class Rewards:
    experience: int
    gold: int
    loot: Item | None
    levels_gained: int


# отчет об экспедиции: с каким сидом, куда, как прошел бой и что получил герой
@dataclass(frozen=True)
class ExpeditionReport:
    seed: int
    location_code: str
    battle: BattleReport
    rewards: Rewards


LOOT_CHANCE = 0.6
ENCHANT_CHANCE = 0.3


class Location(ABC):

    def __init__(self, code: str, display_name: str, recommended_level: int, catalog: ItemCatalog) -> None:
        self._code = code
        self._display_name = display_name
        self._recommended_level = recommended_level
        self._catalog = catalog

    # создание врага делегируется подклассам для повышения гибкости
    @abstractmethod
    def _create_enemy(self) -> Enemy: ...

    # коды предметов из каталога, которые можно найти в локации
    @property
    @abstractmethod
    def _loot_table(self) -> tuple[str, ...]: ...

    # бизнес-логика, общая для всех локаций:
    # герой встречает врага, сражается с ним и получает награду, если победил
    def explore(self, hero: Hero, seed: int | None = None) -> ExpeditionReport:
        dice = Dice()
        if seed is None:
            seed = dice.next_seed()
        dice.reseed(seed)

        hero.restore_health()
        enemy = self._create_enemy()
        battle = Battle(hero, enemy).run()

        if battle.outcome == Outcome.VICTORY:
            rewards = self._reward(hero, enemy, dice)
        else:
            rewards = self._punish(hero)

        return ExpeditionReport(seed, self._code, battle, rewards)

    def _reward(self, hero: Hero, enemy: Enemy, dice: Dice) -> Rewards:
        experience = enemy.experience_reward
        gold = enemy.roll_gold_reward()
        loot = self._roll_loot(dice)

        levels_gained = hero.gain_experience(experience)
        hero.add_gold(gold)
        if loot is not None:
            hero.add_item(loot)

        return Rewards(experience, gold, loot, levels_gained)

    def _roll_loot(self, dice: Dice) -> Item | None:
        if not dice.chance(LOOT_CHANCE):
            return None

        # добыча - это копия шаблона из каталога, ее можно менять, не боясь испортить шаблон
        loot = self._catalog.create(dice.pick(self._loot_table))
        if dice.chance(ENCHANT_CHANCE):
            loot.enchant(dice.pick(loot.possible_enchantments))

        return loot

    # проигравший герой теряет половину золота
    def _punish(self, hero: Hero) -> Rewards:
        lost_gold = hero.gold // 2
        hero.spend_gold(lost_gold)
        return Rewards(0, -lost_gold, None, 0)

    @property
    def code(self) -> str:
        return self._code

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def recommended_level(self) -> int:
        return self._recommended_level


class Forest(Location):

    CODE = "forest"

    def __init__(self, catalog: ItemCatalog) -> None:
        super().__init__(Forest.CODE, "Мистический лес", 1, catalog)

    def _create_enemy(self) -> Enemy:
        return Goblin()

    @property
    def _loot_table(self) -> tuple[str, ...]:
        return (GOBLIN_CLEAVER, HUNTING_BOW, LEATHER_ARMOR)


class Crypt(Location):

    CODE = "crypt"

    def __init__(self, catalog: ItemCatalog) -> None:
        super().__init__(Crypt.CODE, "Заброшенный склеп", 3, catalog)

    def _create_enemy(self) -> Enemy:
        return Skeleton()

    @property
    def _loot_table(self) -> tuple[str, ...]:
        return (KNIGHT_BLADE, BONE_BOW, NECROMANCER_STAFF, CRYPT_MAIL)


class DragonLair(Location):

    CODE = "dragon-lair"

    def __init__(self, catalog: ItemCatalog) -> None:
        super().__init__(DragonLair.CODE, "Логово дракона", 5, catalog)

    def _create_enemy(self) -> Enemy:
        return Dragon()

    @property
    def _loot_table(self) -> tuple[str, ...]:
        return (DAWN_BLADE, DRAGONSCALE_ARMOR)


# все локации игры
class LocationRegistry:

    def __init__(self, locations: Iterable[Location]) -> None:
        self._locations: dict[str, Location] = {}
        for location in locations:
            self._locations[location.code] = location

    def get(self, code: str) -> Location:
        location = self._locations.get(code)
        if location is None:
            raise UnknownCodeError("Локация", code)

        return location

    @property
    def all(self) -> list[Location]:
        return list(self._locations.values())


SELL_PRICE_PERCENT = 50


class Merchant:

    def __init__(self, catalog: ItemCatalog, assortment: Iterable[str]) -> None:
        self._catalog = catalog
        self._assortment = tuple(assortment)

    # образцы товаров, чтобы показать их покупателю
    @property
    def showcase(self) -> list[Item]:
        showcase = []
        for code in self._assortment:
            showcase.append(self._catalog.create(code))

        return showcase

    def buy(self, hero: Hero, code: str) -> Item:
        if code not in self._assortment:
            raise UnknownCodeError("Товар", code)

        # покупатель получает собственную копию предмета из каталога
        item = self._catalog.create(code)
        hero.spend_gold(item.price)
        hero.add_item(item)
        return item

    def sell(self, hero: Hero, item: Item) -> int:
        price = self.sell_price(item)
        hero.remove_item(item)
        hero.add_gold(price)
        return price

    def sell_price(self, item: Item) -> int:
        return item.price * SELL_PRICE_PERCENT // 100
