if __package__:
    from .animal import Animal
else:
    from animal import Animal


class Parrot(Animal):

    def express(self):
        return (
            "   __\n  (o >\n  / /)\n /_/_)\n   ||\n"
            "Попугай говорит: Кар!"
        )

    def get_age_in_human_years(self):
        return self.get_age() * 5
