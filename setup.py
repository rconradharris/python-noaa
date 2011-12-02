from setuptools import setup, find_packages
from setuptools.command.sdist import sdist

import noaa

setup(
    name='noaa',
    version=noaa.__version__,
    description='Python Bindings to the NOAA National Digital Forecast '
                'Database (NDFD)',
    license='MIT License',
    author='Rick Harris',
    author_email='rconradharris@gmail.com',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.6'
    ],
    install_requires=[],
    scripts=["bin/noaa"])
