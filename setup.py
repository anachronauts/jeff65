from setuptools import setup, find_packages

setup(
    name='jeff65',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'antlr4-python3-runtime>=4.5.2',
    ],
    entry_points={
        'console_scripts': [
            'jeff65 = jeff65:main'
        ]
    }
)
