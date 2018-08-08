from setuptools import setup, find_packages

setup(
    name='jeff65',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'attrs>=18.1.0',
    ],
    entry_points={
        'console_scripts': [
            'jeff65 = jeff65:main'
        ]
    }
)
