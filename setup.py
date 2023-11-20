from setuptools import setup, find_packages

install_requires = [
    "flask-sqlalchemy >= 2.3.0",
    "sqlalchemy_utils>=0.30",
    "flask>=1.0.0",
    "sqlalchemy>=1.3,<2",
    "serialchemy>=0.3.0",
]

extras_require = {
    "docs": ["sphinx >= 1.4", "sphinx_rtd_theme"],
    "testing": ["codecov", "pytest", "pytest-cov", "pytest-mock", "pytest-regressions", "tox"],
}

setup(
    name="flask-restalchemy",
    use_scm_version={"git_describe_command": "git describe --dirty --tags --long --match v*"},
    setup_requires=["setuptools_scm"],
    packages=find_packages("src"),
    package_dir={"": "src"},
    package_data={"": ["**/*.yml"]},
    url="https://github.com/ESSS/flask-restalchemy",
    license="MIT",
    author="ESSS",
    author_email="foss@esss.co",
    description="Flask extension to build REST APIs based on SQLAlchemy models ",
    keywords="flask sqlalchemy orm",
    license_files=('LICENSE',),
    install_requires=install_requires,
    extras_require=extras_require,
    python_requires=">=3.6",
    classifiers=[
        "Environment :: Web Environment",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Database :: Front-Ends",
        "Topic :: Internet :: WWW/HTTP",
    ],
)
