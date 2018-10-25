from setuptools import setup, find_packages

setup(
    name='words_to_number',
    version='1.0',
    description='Convert English text representation of numbers to numerical representation',
    author='Greg Werbin',
    author_email='outthere@me.gregwerbin.com',
    license='MIT',
    url='https://github.com/gwerbin/word_to_number',
    packages=find_packages(exclude=['test'])
)
