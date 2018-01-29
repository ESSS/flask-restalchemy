from setuptools import setup

install_requires=[
    'flask-restful>=0.3.0',
    'flask-sqlalchemy >= 2.3.0',
    'marshmallow-sqlalchemy >= 0.13.0',
]

setup(
    name='flask-rest-orm',
    version='0.2.0',
    packages=['flask_rest_orm', 'flask_rest_orm.resources'],
    url='https://github.com/ESSS/flask-rest-orm',
    license='MIT',
    author='ESSS Ltda',
    author_email='igor@esss.com.br',
    description='Flask extension to build REST APIs based on SQLAlchemy models ',
    keywords='flask sqlalchemy orm',
    data_files = [("", ["LICENSE"])],
    install_requires=install_requires,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Database :: Front-Ends',
        'Topic :: Internet :: WWW/HTTP',
    ],
)
