from setuptools import setup, find_packages

setup(
    name='earthsaver',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'click',
    ],
    entry_points={
        'console_scripts': [
            'earthsaver=earthsaver.main:earthsaver',
        ],
    },
    author='Your Name',  # 선택 사항
    author_email='your.email@example.com',  # 선택 사항
    description='A CLI tool for refactoring Java code and measuring carbon footprint.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/earthsaver',  # 선택 사항
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
