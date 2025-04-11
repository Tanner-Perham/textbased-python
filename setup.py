from setuptools import setup, find_packages

setup(
    name="textbased-python",
    version="0.1",
    packages=find_packages(include=['game', 'dialogue', 'ui', 'save', 'config', 'core', 'character', 'quest']),
    install_requires=[
        "textual>=0.1.18",
        "pyyaml>=6.0",
        "pytest>=7.0.0",
    ],
    python_requires=">=3.13",
) 