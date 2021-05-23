import datetime
import inflect


class DefaultTranslator:
    def __init__(self, name: str, origin: datetime.date, target: datetime.date):
        self.name = name
        self.origin = origin
        self.target = target

    @property
    def age(self) -> int:
        return self.target.year - self.origin.year

    @property
    def description(self) -> str:
        raise NotImplementedError

    @property
    def origin_full(self) -> str:
        return f'{self.origin:%B} {self.origin.day}, {self.origin.year}'

    @property
    def summary(self) -> str:
        raise NotImplementedError

    @property
    def target_full(self) -> str:
        return f'{self.target:%A, %B} {self.target.day}, {self.target.year}'


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
            return f'{self.name} was born on {self.target_full}'
        else:
            return f'{self.name}, born {self.origin_full}, will turn {self.age} on {self.target_full}'


class EnglishAnniversaryTranslator(DefaultTranslator):
    inf = inflect.engine()

    @property
    def summary(self) -> str:
        if self.origin.year == 1:
            return f"{self.name}'s anniversary"
        elif self.age == 0:
            return f'{self.name} get married'
        else:
            return f'{self.name} celebrate their {self.inf.ordinal(self.age)} anniversary'

    @property
    def description(self) -> str:
        if self.origin.year == 1:
            return (f'{self.name}, married on {self.origin:%B} {self.origin.day}, '
                    f'will celebrate an anniversary on {self.target_full}')
        elif self.age == 0:
            return f'{self.name} got married on {self.target_full}'
        else:
            return (f'{self.name}, married on {self.origin_full}, '
                    f'will celebrate their {self.inf.ordinal(self.age)} anniversary on {self.target_full}')
