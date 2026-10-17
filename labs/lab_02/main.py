if __package__:
    from .parrot import Parrot
    from .turtle import Turtle
    from .person import Person
else:
    from parrot import Parrot
    from turtle import Turtle
    from person import Person


def main():
    parrot = Parrot("Кеша", 3)
    turtle = Turtle("Тортила", 5)

    person1 = Person("Анна", parrot)
    person2 = Person("Иван")

    person1.show_info()
    person2.show_info()

    person2.set_pet(turtle)
    person2.show_info()


if __name__ == "__main__":
    main()
