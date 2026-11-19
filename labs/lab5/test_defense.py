import unittest
from unittest.mock import Mock, patch

from labs.lab4.patterns import Damage, Dodge, Shield


class TestDefense(unittest.TestCase):
    """Поведенческий паттерн: цепочка обработчиков защиты."""

    def test_shield_boundaries(self):
        for incoming, absorbed, remaining in ((0, 0, 0), (29, 29, 0),
                                               (30, 30, 0), (31, 30, 1),
                                               (40, 30, 10)):
            with self.subTest(incoming=incoming):
                result = Shield(30).apply(Damage(incoming))
                self.assertEqual(result.absorbed, absorbed)
                self.assertEqual(result.amount, remaining)
                self.assertFalse(result.evaded)

    def test_damage_passes_through_every_handler(self):
        chain = Shield(3, Shield(2))
        damage = Damage(10)
        self.assertIs(chain.apply(damage), damage)
        self.assertEqual(damage.absorbed, 5)
        self.assertEqual(damage.amount, 5)

    @patch("labs.lab4.patterns.Dice")
    def test_successful_dodge_stops_chain(self, dice_class):
        dice_class.return_value.chance.return_value = True
        following = Mock()
        damage = Damage(20)
        self.assertIs(Dodge(0.3, following).apply(damage), damage)
        self.assertTrue(damage.evaded)
        self.assertEqual(damage.amount, 0)
        dice_class.return_value.chance.assert_called_once_with(0.3)
        following.apply.assert_not_called()

    @patch("labs.lab4.patterns.Dice")
    def test_failed_dodge_forwards_same_damage(self, dice_class):
        dice_class.return_value.chance.return_value = False
        following = Mock()
        damage = Damage(20)
        following.apply.return_value = damage
        result = Dodge(0.3, following).apply(damage)
        self.assertIs(result, damage)
        self.assertFalse(damage.evaded)
        following.apply.assert_called_once_with(damage)


if __name__ == "__main__":
    unittest.main()
