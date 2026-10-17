if __package__:
    from .pet import Pet
else:
    from pet import Pet


class Animal(Pet):

    def __init__(self, name, age):
        self.__name = name
        self.__age = age

    def get_name(self):
        return self.__name

    def get_age(self):
        return self.__age
    def happy_birthday(self):
        self.__age += 1
