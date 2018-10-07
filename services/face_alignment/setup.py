from setuptools import setup, find_packages

with open('requirements.txt') as f:
  reqs = list(f.read().strip().split('\n'))

setup(
    name='face_alignment',
    version='1.0.0',
    packages=find_packages(exclude=('test',)),
    install_requires=reqs,
)