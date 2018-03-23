try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='words_to_number',
    version='1.0',
    description='Convert English text representation of numbers to numerical representation',
    author='Greg Werbin and Rocketrip',
    author_email='greg@rocketrip.com',
    license='MIT',
    url='https://github.com/greg-rocketrip/word_to_number',
    packages=['words_to_number']
)
