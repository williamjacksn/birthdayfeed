import datetime


class DefaultTranslator:
    def __init__(self, name: str, origin: datetime.date, target: datetime.date):
        self.name = name
        self.origin = origin
        self.target = target

    @property
    def age(self) -> int:
        return self.target.year - self.origin.year


class EnglishBirthdayTranslator(DefaultTranslator):
    @property
    def summary(self) -> str:
        if self.origin.year == 1:
            return f"{self.name}'s birthday"
        elif self.age == 0:
            return f'{self.name} is born'
        else:
            return f'{self.name} turns {self.age}'

    @property
    def description(self) -> str:
        if self.origin.year == 1:
            return (f'{self.name}, born {self.origin:%B} {self.origin.day}, '
                    f'will celebrate a birthday on {self.target_full}')
        elif self.age == 0:
            return f'{self.name} was born on {self.target:%A, %B} {self.target.day}, {self.target.year}'
        else:
            return (f'{self.name}, born {self.origin:%B} {self.origin.day}, {self.origin.year}, '
                    f'will turn {self.age} on {self.target_full}')

    @property
    def target_full(self) -> str:
        return f'{self.target:%A, %B} {self.target.day}, {self.target.year}'
