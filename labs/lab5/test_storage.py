import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

from labs.lab4.hero import Hero
from labs.lab4.items import SHARP, STURDY, create_default_catalog
from labs.lab4.kits import HeroClass
from labs.lab4.patterns import CachedSave, JsonSave


def create_hero():
    catalog = create_default_catalog()
    return (Hero.Builder().set_name("Артур").set_hero_class(HeroClass.WARRIOR)
            .set_starter_kit(HeroClass.WARRIOR.starter_kit(catalog)).build())


class TestCachedSave(unittest.TestCase):
    """Структурный паттерн Proxy с подменённым хранилищем."""

    def test_lazy_loading_and_single_storage_read(self):
        storage = Mock()
        storage.load.return_value = create_hero()
        cache = CachedSave(storage)
        storage.load.assert_not_called()
        first = cache.load()
        second = cache.load()
        storage.load.assert_called_once_with()
        self.assertEqual(first.name, second.name)
        self.assertIsNot(first, second)

    def test_save_updates_storage_and_cache(self):
        storage = Mock()
        cache = CachedSave(storage)
        hero = create_hero()
        cache.save(hero)
        storage.save.assert_called_once_with(hero)
        hero.add_gold(100)
        self.assertEqual(cache.load().gold, 50)
        storage.load.assert_not_called()

    def test_failed_save_does_not_update_cache(self):
        storage = Mock()
        storage.load.return_value = create_hero()
        cache = CachedSave(storage)
        cache.load()
        changed = create_hero()
        changed.add_gold(100)
        storage.save.side_effect = OSError("disk error")
        with self.assertRaises(OSError):
            cache.save(changed)
        self.assertEqual(cache.load().gold, 50)


class TestJsonSave(unittest.TestCase):
    """Интеграция: настоящее JSON-хранилище и файловая система."""

    def test_hero_round_trip(self):
        catalog = create_default_catalog()
        hero = create_hero()
        hero.gain_experience(45)
        hero.add_gold(25)
        hero.weapon.enchant(SHARP)
        hero.armor.enchant(STURDY)
        hero.add_item(catalog.create("iron-sword"))
        hero.achievements.append("Первая кровь")
        with TemporaryDirectory() as directory:
            path = Path(directory) / "hero.json"
            storage = JsonSave(path, catalog)
            storage.save(hero)
            self.assertTrue(path.is_file())
            restored = JsonSave(path, catalog).load()
        self.assertEqual((restored.name, restored.hero_class, restored.level,
                          restored.experience, restored.gold),
                         (hero.name, hero.hero_class, hero.level,
                          hero.experience, hero.gold))
        self.assertEqual(restored.weapon.code, hero.weapon.code)
        self.assertEqual(restored.weapon.enchantments, hero.weapon.enchantments)
        self.assertEqual(restored.armor.enchantments, hero.armor.enchantments)
        self.assertEqual([item.code for item in restored.inventory],
                         [item.code for item in hero.inventory])
        self.assertEqual(restored.achievements, hero.achievements)

    def test_missing_save_raises_file_not_found(self):
        with TemporaryDirectory() as directory:
            storage = JsonSave(Path(directory) / "missing.json", create_default_catalog())
            with self.assertRaises(FileNotFoundError):
                storage.load()


if __name__ == "__main__":
    unittest.main()
