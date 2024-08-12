from setuptools import setup, find_packages

with open("README.md", "r") as f:
    description = f.read()

setup(
    name='weedout', 
    version='1.0', 
    packages=find_packages(), 
    install_requires=[
        'pandas',
        'numpy',
        'seaborn',
        'matplotlib',
        'scikit-learn',
        'statsmodels',
        'imbalanced-learn',
        'scipy',
        'typing'
    ],
    long_description=description,
    long_description_content_type ="text/markdown",

)