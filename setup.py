from setuptools import setup, find_packages

setup(
    name='r_subproc',
    version='0.0.1',
    url='https://github.com/pnewstein/r_subproc.git',
    author='Peter Newstein',
    author_email='peternewstein@gmail.com',
    description='A library to manage a R process to execute R code from python',
    packages=find_packages(),
    install_requires=["pydantic"],
)
