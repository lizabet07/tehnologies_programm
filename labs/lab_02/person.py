class Person:

    def __init__(self, name, pet=None):
        self.__name = name
        self.__pet = pet

    def get_name(self):
        return self.__name

    def get_pet(self):
        return self.__pet

    def set_pet(self, pet):
        self.__pet = pet

    def show_info(self):
        print("Человек:", self.__name)

        if self.__pet is None:
            print("Питомца нет")
        else:
            print("Питомец:", self.__pet.get_name())
            print("Возраст:", self.__pet.get_age())
            print("Возраст в человеческих годах:",
                  self.__pet.get_age_in_human_years())
            print(self.__pet.express())

        print()
