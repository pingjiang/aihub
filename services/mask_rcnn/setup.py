from setuptools import setup, find_packages

with open('requirements.txt') as f:
  reqs = list(f.read().strip().split('\n'))

setup(
    name='aihub_mask_rcnn',
    version='1.0.0',
    packages=find_packages(exclude=('test','src')),
    install_requires=reqs,
)