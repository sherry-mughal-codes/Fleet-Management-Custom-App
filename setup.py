from setuptools import setup, find_packages

setup(
    name="fleet_management",
    version="0.0.1",
    description="Production-Grade Enterprise Fleet Management System for Frappe Framework v15",
    author="Fleet Management Team",
    author_email="developer@fleetmanagement.local",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        "pydantic>=2.0.0"
    ]
)
