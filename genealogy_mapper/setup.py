from setuptools import setup, find_packages

setup(
    name="genealogy_mapper",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests>=2.31.0",
        "validators>=0.22.0",
        "python-dateutil>=2.8.2",
        "rich>=13.7.0",
        "beautifulsoup4>=4.12.3",
        "click>=8.1.7"
    ],
    entry_points={
        "console_scripts": [
            "genealogy-mapper=genealogy_mapper.cli:cli",
        ],
    },
    python_requires=">=3.8",
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool for processing and managing genealogy data",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/genealogy_mapper",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
) 