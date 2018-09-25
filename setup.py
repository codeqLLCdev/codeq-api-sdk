from distutils.core import setup
import codeq_nlp_api

version = codeq_nlp_api.__version__

setup(
    name='codeq-nlp-api',
    packages=['codeq-nlp-api'],
    version=version,
    license='Apache license 2.0',
    description='Codeq NLP API SDK for Python',
    author='Codeq, LLC',
    author_email='rodrigo@codeq.com',
    url='http://api.codeq.com:8880/',
    download_url='https://github.com/codeqLLCdev/codeq-api-sdk/archive/v0.1.0.tar.gz',
    keywords=['codeq', 'nlp', 'api', 'natural language processing'],
    install_requires=[
        'requests',
    ],
    classifiers=[
        # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Natural Language Processing',
        'License :: OSI Approved :: Apache license 2.0',
        'Programming Language :: Python :: 3',
    ],
)
