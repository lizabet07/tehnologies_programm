if __package__:
    from .animal import Animal
else:
    from animal import Animal


class Turtle(Animal):

    def express(self):
        return (
            "    _____\n __/     \\__\n(o  _____   _)\n   /_/   \\_\\\n"
            "Черепаха молчит"
        )

    def get_age_in_human_years(self):
        if self.get_age() == 1:
            return 15
        return 15 + (self.get_age() - 1) * 2
