from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
import copy
import json

from .combat import Combatant, Hit, Outcome
from .dice import Dice
from .enemies import Enemy
from .hero import Hero
from .items import FOR_ARMOR, FOR_WEAPONS, Weapon
from .kits import HeroClass


@dataclass
class Damage:
    amount: int
    evaded: bool = False
    absorbed: int = 0


# Цепочка: каждый обработчик изменяет урон и передаёт его дальше.
class Defense:
    def __init__(self, next_defense=None):
        self.next = next_defense

    def apply(self, damage: Damage) -> Damage:
        self.handle(damage)
        return self.next.apply(damage) if self.next and not damage.evaded else damage

    def handle(self, damage: Damage) -> None:
        pass


class Dodge(Defense):
    def __init__(self, chance: float, next_defense=None):
        super().__init__(next_defense)
        self.chance = chance

    def handle(self, damage: Damage) -> None:
        if Dice().chance(self.chance):
            damage.amount = 0
            damage.evaded = True


class Shield(Defense):
    def __init__(self, points: int, next_defense=None):
        super().__init__(next_defense)
        self.points = points

    def handle(self, damage: Damage) -> None:
        absorbed = min(self.points, damage.amount)
        damage.amount -= absorbed
        damage.absorbed += absorbed


class FighterWrapper(Combatant):
    def __init__(self, inner: Combatant):
        self.inner = inner

    @property
    def code(self): return self.inner.code
    @property
    def name(self): return self.inner.name
    @property
    def health(self): return self.inner.health
    @property
    def max_health(self): return self.inner.max_health
    def is_alive(self): return self.inner.is_alive()
    def roll_damage(self): return self.inner.roll_damage()
    def receive_hit(self, damage): return self.inner.receive_hit(damage)


# Стратегия влияет на урон героя и входящий урон.
class Strategy(ABC):
    attack_factor = 1.0
    defense_factor = 1.0


class Balanced(Strategy): pass
class Aggressive(Strategy):
    attack_factor = 1.5
    defense_factor = 1.25
class Cautious(Strategy):
    attack_factor = 0.8
    defense_factor = 0.7


class StrategyFighter(FighterWrapper):
    def __init__(self, inner, strategy):
        super().__init__(inner)
        self.strategy = strategy
        self.defense = Dodge(0.1, Shield(1))

    def roll_damage(self):
        hit = self.inner.roll_damage()
        return Hit(max(1, round(hit.damage * self.strategy.attack_factor)), hit.critical)

    def receive_hit(self, damage):
        result = self.defense.apply(Damage(max(0, round(damage * self.strategy.defense_factor))))
        return self.inner.receive_hit(result.amount) if result.amount else 0


# Декораторы можно вкладывать друг в друга, сохраняя интерфейс врага.
class EnemyDecorator(FighterWrapper, Enemy):
    @property
    def experience_reward(self): return self.inner.experience_reward
    def roll_gold_reward(self): return self.inner.roll_gold_reward()


class StrongEnemy(EnemyDecorator):
    @property
    def name(self): return self.inner.name + " (сильный)"
    def roll_damage(self):
        hit = self.inner.roll_damage()
        return Hit(round(hit.damage * 1.5), hit.critical)


class ArmoredEnemy(EnemyDecorator):
    def __init__(self, inner):
        super().__init__(inner)
        self.defense = Shield(3)
    @property
    def name(self): return self.inner.name + " (бронированный)"
    def receive_hit(self, damage):
        result = self.defense.apply(Damage(damage))
        return self.inner.receive_hit(result.amount) if result.amount else 0


class DoubleAttackEnemy(EnemyDecorator):
    @property
    def name(self): return self.inner.name + " (двойная атака)"
    def roll_damage(self):
        first, second = self.inner.roll_damage(), self.inner.roll_damage()
        return Hit(first.damage + second.damage, first.critical or second.critical)


def enhance_enemy(enemy):
    for decorator in (StrongEnemy, ArmoredEnemy, DoubleAttackEnemy):
        if Dice().chance(0.25):
            enemy = decorator(enemy)
    return enemy


# Адаптер превращает оружие в противника с боевым интерфейсом.
class PossessedWeapon(Enemy):
    def __init__(self, weapon: Weapon):
        self.weapon = weapon
        self._health = 90
    @property
    def code(self): return "possessed-weapon"
    @property
    def name(self): return "Одержимое оружие: " + self.weapon.name
    @property
    def health(self): return self._health
    @property
    def max_health(self): return 90
    @property
    def experience_reward(self): return 100
    def roll_gold_reward(self): return Dice().roll(40, 80)
    def is_alive(self): return self._health > 0
    def roll_damage(self): return self.weapon.roll_damage()
    def receive_hit(self, damage):
        dealt = max(1, damage)
        self._health = max(0, self._health - dealt)
        return dealt


class AchievementObserver:
    def update(self, hero, report):
        rewards = report.rewards
        achieved = []
        if report.battle.outcome == Outcome.VICTORY:
            achieved.append("Первая кровь")
            if report.battle.enemy.code == "dragon": achieved.append("Драконоборец")
        if rewards.loot and rewards.loot.enchantments: achieved.append("Счастливчик")
        if hero.level >= 5: achieved.append("Ветеран")
        for achievement in achieved:
            if achievement not in hero.achievements:
                hero.achievements.append(achievement)


class JournalObserver:
    def __init__(self): self.entries = []
    def update(self, hero, report):
        self.entries.append(f"{report.location_code}: {report.battle.outcome.value}, seed={report.seed}")


def item_data(item):
    return {"code": item.code, "enchantments": [e.code for e in item.enchantments]}


class JsonSave:
    def __init__(self, path, catalog):
        self.path, self.catalog = Path(path), catalog

    def save(self, hero):
        data = {"name": hero.name, "class": hero.hero_class.code, "level": hero.level,
                "experience": hero.experience, "gold": hero.gold,
                "weapon": item_data(hero.weapon), "armor": item_data(hero.armor),
                "inventory": [item_data(item) for item in hero.inventory],
                "achievements": hero.achievements}
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf8")

    def load(self):
        data = json.loads(self.path.read_text(encoding="utf8"))
        def item(value):
            result = self.catalog.create(value["code"])
            enchantments = {e.code: e for e in FOR_ARMOR + FOR_WEAPONS}
            for code in value["enchantments"]: result.enchant(enchantments[code])
            return result
        hero_class = next(c for c in HeroClass if c.code == data["class"])
        return (Hero.Builder().set_name(data["name"]).set_hero_class(hero_class)
                .set_level(data["level"]).set_gold(data["gold"]).set_experience(data["experience"])
                .set_weapon(item(data["weapon"])).set_armor(item(data["armor"]))
                .set_inventory([item(i) for i in data["inventory"]])
                .set_achievements(data["achievements"]).build())


# Заместитель кэширует снимок, возвращая независимую копию.
class CachedSave:
    def __init__(self, storage):
        self.storage, self._cache = storage, None
    def save(self, hero):
        self.storage.save(hero)
        self._cache = copy.deepcopy(hero)
    def load(self):
        if self._cache is None: self._cache = self.storage.load()
        return copy.deepcopy(self._cache)


# Фасад объединяет экспедицию, подписчиков и сохранение.
class GameFacade:
    def __init__(self, locations, storage):
        self.locations, self.storage = locations, storage
        self.journal = JournalObserver()
        self.observers = [AchievementObserver(), self.journal]
    def explore(self, hero, location, strategy, seed=None):
        report = location.explore(hero, seed, strategy)
        for observer in self.observers: observer.update(hero, report)
        return report
    def save(self, hero): self.storage.save(hero)
    def load(self): return self.storage.load()
