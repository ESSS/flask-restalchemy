from setuptools import setup, find_packages

install_requires=[
    'flask-restful>=0.3.0',
    'flask-sqlalchemy >= 2.3.0',
]

setup(
    name='flask-rest-orm',
    version='0.5.0',
    packages=find_packages(exclude=['*.tests']),
    url='https://github.com/ESSS/flask-rest-orm',
    license='MIT',
    author='ESSS Ltda',
    author_email='igor@esss.com.br',
    description='Flask extension to build REST APIs based on SQLAlchemy models ',
    keywords='flask sqlalchemy orm',
    data_files=[("", ["LICENSE"])],
    install_requires=install_requires,
    python_requires='>=3.4',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Database :: Front-Ends',
        'Topic :: Internet :: WWW/HTTP',
    ],
)
