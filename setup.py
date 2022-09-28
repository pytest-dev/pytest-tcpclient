from setuptools import setup, find_packages


setup(
    name="mocktcp",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    license="MIT",
)
