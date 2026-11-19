from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


# удар: сколько урона и был ли он критическим
@dataclass(frozen=True)
class Hit:
    damage: int
    critical: bool


# всё, что может участвовать в бою: и герой, и враги
class Combatant(ABC):

    # код вида сущности: класс героя или тип врага
    @property
    @abstractmethod
    def code(self) -> str: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def health(self) -> int: ...

    @property
    @abstractmethod
    def max_health(self) -> int: ...

    @abstractmethod
    def is_alive(self) -> bool: ...

    # удар, который будет нанесен данной сущностью
    @abstractmethod
    def roll_damage(self) -> Hit: ...

    # получение удара, возвращает урон, который прошел на самом деле
    @abstractmethod
    def receive_hit(self, damage: int) -> int: ...


class Side(Enum):
    HERO = "hero"
    ENEMY = "enemy"


class EventType(Enum):
    HIT = "hit"
    CRITICAL_HIT = "critical_hit"
    DEATH = "death"


class Outcome(Enum):
    VICTORY = "victory"
    DEFEAT = "defeat"


@dataclass(frozen=True)
class BattleEvent:
    round: int
    type: EventType
    source: Side
    target: Side
    amount: int
    target_health_after: int


# участник боя в том виде, в котором он попадает в отчет
@dataclass(frozen=True)
class Participant:
    code: str
    name: str
    max_health: int

    @staticmethod
    def of(combatant: Combatant) -> Participant:
        return Participant(combatant.code, combatant.name, combatant.max_health)


# результат боя: кто сражался, чем все закончилось и что происходило по ходу дела
@dataclass(frozen=True)
class BattleReport:
    hero: Participant
    enemy: Participant
    outcome: Outcome
    events: tuple[BattleEvent, ...]


# бой идет по раундам: сначала бьет герой, потом враг, пока кто-то не погибнет
class Battle:

    def __init__(self, hero: Combatant, enemy: Combatant) -> None:
        self._hero = hero
        self._enemy = enemy
        self._events: list[BattleEvent] = []
        self._round = 0

    def run(self) -> BattleReport:
        while self._hero.is_alive() and self._enemy.is_alive():
            self._round += 1
            self._strike(self._hero, Side.HERO, self._enemy, Side.ENEMY)
            if self._enemy.is_alive():
                self._strike(self._enemy, Side.ENEMY, self._hero, Side.HERO)

        outcome = Outcome.VICTORY if self._hero.is_alive() else Outcome.DEFEAT
        return BattleReport(
            Participant.of(self._hero), Participant.of(self._enemy), outcome, tuple(self._events)
        )

    def _strike(self, attacker: Combatant, source: Side, defender: Combatant, target: Side) -> None:
        hit = attacker.roll_damage()
        dealt = defender.receive_hit(hit.damage)
        event_type = EventType.CRITICAL_HIT if hit.critical else EventType.HIT
        self._emit(BattleEvent(self._round, event_type, source, target, dealt, defender.health))

        if not defender.is_alive():
            self._emit(BattleEvent(self._round, EventType.DEATH, source, target, 0, 0))

    def _emit(self, event: BattleEvent) -> None:
        self._events.append(event)
