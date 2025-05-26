"""
Setup script for the genealogy package.
"""

from setuptools import setup, find_packages

setup(
    name="genealogy",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'requests>=2.25.1',
        'beautifulsoup4>=4.9.3',
    ],
    entry_points={
        'console_scripts': [
            'genealogy=genealogy.main:main',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A package for processing genealogical data from obituaries",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/genealogy",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
) 