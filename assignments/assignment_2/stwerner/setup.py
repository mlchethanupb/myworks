from setuptools import setup, find_packages


with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='common-utils',
    version='0.0.0',
    author='stwerner97',
    description="Solution to the second assignment.",
    package_dir={'': 'flowsim'},
    packages=find_packages('flowsim'),
    install_requires=requirements,
    zip_safe=False,
)
