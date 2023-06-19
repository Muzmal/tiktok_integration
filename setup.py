from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in tiktok_integration/__init__.py
from tiktok_integration import __version__ as version

setup(
	name="tiktok_integration",
	version=version,
	description="Tiktok shop data in ERPNext",
	author="Zaviago",
	author_email="muzammal.rasool1079@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
