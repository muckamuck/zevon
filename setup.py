from setuptools import setup


setup(
    name='Zevon',
    version='0.2.2',
    packages=['zevon'],
    description='Zevon - turn a API Gateway / Lambda event to a Flask thing',
    author='Chuck Muckamuck (obviously a pseudonym)',
    author_email='Chuck.Muckamuck@gmail.com',
    install_requires=[
        'Flask<=2.0.2',
        'Werkzeug<=2.0.3'
    ]
)
