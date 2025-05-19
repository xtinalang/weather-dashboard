from setuptools import find_packages, setup

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="weather-dashboard",
    version="0.1.0",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "weather-dashboard=web.app:app",
        ],
    },
)
