from setuptools import setup, find_packages


requirements = [
    'networkx',
    'PyYAML',
    'numpy'
    'simpy'

]

test_requirements = [
    'flake8'
]


setup(
    name='common-utils',
    version='0.0.0',
    author='AICON',
    description="Assignment 2.",
    package_dir={'': 'flowsim'},
    packages=find_packages('flowsim'),
    install_requires=requirements + test_requirements,
    tests_require=test_requirements,
    zip_safe=False,
)
