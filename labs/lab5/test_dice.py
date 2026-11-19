import unittest

from labs.lab4.dice import Dice


class TestDice(unittest.TestCase):
    """Порождающий паттерн Singleton и правила случайных бросков."""

    def setUp(self):
        Dice().reseed(2026)

    def test_singleton(self):
        self.assertIs(Dice(), Dice())

    def test_roll_within_bounds_and_equal_bounds(self):
        for _ in range(100):
            value = Dice().roll(1, 6)
            self.assertGreaterEqual(value, 1)
            self.assertLessEqual(value, 6)
        self.assertEqual(Dice().roll(7, 7), 7)

    def test_impossible_and_certain_chance(self):
        for _ in range(100):
            self.assertFalse(Dice().chance(0))
            self.assertTrue(Dice().chance(1))

    def test_pick_returns_one_of_the_options(self):
        item = object()
        self.assertIs(Dice().pick([item]), item)
        options = ("sword", "shield", "staff")
        for _ in range(100):
            self.assertIn(Dice().pick(options), options)

    def test_reseed_repeats_sequence(self):
        Dice().reseed(42)
        first = [Dice().roll(1, 100) for _ in range(10)]
        Dice().reseed(42)
        self.assertEqual(first, [Dice().roll(1, 100) for _ in range(10)])


if __name__ == "__main__":
    unittest.main()
