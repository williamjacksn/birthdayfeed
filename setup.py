from setuptools import find_packages, setup


setup(
    name='birthdayfeed',
    version='1.0.2',
    description='Subscribe to birthdays in a feed reader or a calendar',
    url='https://github.com/williamjacksn/birthdayfeed',
    author='William Jackson',
    author_email='william@subtlecoolness.com',
    install_requires=['Flask', 'icalendar', 'requests', 'waitress'],
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'birthdayfeed = birthdayfeed.birthdayfeed:main'
        ]
    }
)
