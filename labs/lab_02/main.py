from abc import ABC, abstractmethod


class Pet(ABC):

    @abstractmethod
    def express(self):
        pass

    @abstractmethod
    def get_name(self):
        pass

    @abstractmethod
    def get_age(self):
        pass

    @abstractmethod
    def get_age_in_human_years(self):
        pass

class Animal(Pet):

    def __init__(self, name, age):
        self.name = name
        self.age = age

    def get_name(self):
        return self.name

    def get_age(self):
        return self.age

class Parrot(Animal):

    def express(self):
        return "Попугай говорит: Кар!"

    def get_age_in_human_years(self):
        return self.age * 5


class Turtle(Animal):

    def express(self):
        return "Черепаха молчит"

    def get_age_in_human_years(self):
        if self.age == 1:
            return 15
        return 15 + (self.age - 1) * 2

class Person:

    def __init__(self, name, pet=None):
        self.name = name
        self.pet = pet

    def set_pet(self, pet):
        self.pet = pet

    def show_info(self):
        print("Человек:", self.name)

        if self.pet is None:
            print("Питомца нет")
        else:
            print("Питомец:", self.pet.get_name())
            print("Возраст:", self.pet.get_age())
            print("Возраст в человеческих годах:",
                  self.pet.get_age_in_human_years())
            print(self.pet.express())

        print()

parrot = Parrot("Кеша", 3)
turtle = Turtle("Тортила", 5)

person1 = Person("Анна", parrot)
person2 = Person("Иван")

person1.show_info()
person2.show_info()

person2.set_pet(turtle)
person2.show_info()