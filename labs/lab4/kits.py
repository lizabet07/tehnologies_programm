from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from .dice import UnknownCodeError
from .items import APPRENTICE_STAFF, Armor, CHAINMAIL, HUNTING_BOW, ItemCatalog, LEATHER_ARMOR, LINEN_ROBE, TRAINING_SWORD, Weapon


# Абстрактная фабрика: стартовый набор снаряжения
class StarterKitFactory(ABC):

    # возвращает некое оружие
    @abstractmethod
    def create_weapon(self) -> Weapon: ...

    # возвращает некую броню
    @abstractmethod
    def create_armor(self) -> Armor: ...


class WarriorKitFactory(StarterKitFactory):

    def __init__(self, catalog: ItemCatalog) -> None:
        self._catalog = catalog

    def create_weapon(self) -> Weapon:
        return self._catalog.create_weapon(TRAINING_SWORD)

    def create_armor(self) -> Armor:
        return self._catalog.create_armor(CHAINMAIL)


class RangerKitFactory(StarterKitFactory):

    def __init__(self, catalog: ItemCatalog) -> None:
        self._catalog = catalog

    def create_weapon(self) -> Weapon:
        return self._catalog.create_weapon(HUNTING_BOW)

    def create_armor(self) -> Armor:
        return self._catalog.create_armor(LEATHER_ARMOR)


class MageKitFactory(StarterKitFactory):

    def __init__(self, catalog: ItemCatalog) -> None:
        self._catalog = catalog

    def create_weapon(self) -> Weapon:
        return self._catalog.create_weapon(APPRENTICE_STAFF)

    def create_armor(self) -> Armor:
        return self._catalog.create_armor(LINEN_ROBE)


class HeroClass(Enum):

    # значение каждого класса: код, название, стартовое здоровье и класс фабрики стартового набора
    WARRIOR = ("warrior", "Воин", 120, WarriorKitFactory)
    RANGER = ("ranger", "Следопыт", 100, RangerKitFactory)
    MAGE = ("mage", "Маг", 85, MageKitFactory)

    def __init__(self, code: str, display_name: str, base_health: int, kit_factory: type[StarterKitFactory]) -> None:
        self.code = code
        self.display_name = display_name
        self.base_health = base_health
        self._kit_factory = kit_factory

    # каждый класс сам знает свою фабрику стартового снаряжения
    def starter_kit(self, catalog: ItemCatalog) -> StarterKitFactory:
        return self._kit_factory(catalog)

    @classmethod
    def by_code(cls, code: str) -> HeroClass:
        for hero_class in cls:
            if hero_class.code == code:
                return hero_class

        raise UnknownCodeError("Класс героя", code)
