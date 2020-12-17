from distutils.core import setup

__version__ = "2.4.0"

download_url = "https://github.com/codeqLLCdev/codeq-api-sdk/archive/v%s.tar.gz" % __version__

setup(
    name='codeq-nlp-api',
    packages=['codeq_nlp_api'],
    version=__version__,
    license='Apache license 2.0',
    description='Codeq NLP API SDK for Python',
    author='Codeq, LLC',
    author_email='rodrigo@codeq.com',
    url='https://api.codeq.com',
    download_url=download_url,
    keywords=['codeq', 'nlp', 'api', 'natural language processing'],
    install_requires=[
        'requests',
    ],
    classifiers=[
        # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
)
