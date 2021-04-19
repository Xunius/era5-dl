import setuptools
import codecs
import os.path

with open('README.md', 'r') as fin:
    long_description=fin.read()
#exec(open('version.py').read())


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()

def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


setuptools.setup(
        name='era5dl',
        #version=__version__,
        version=get_version("era5dl/__init__.py"),
        author='Guangzhi XU',
        author_email='xugzhi1987@gmail.com',
        description="a simple helper for downloading ECMWF's ERA5 reanalysis data",
        long_description=long_description,
        long_description_content_type='text/markdown',
        url='https://github.com/Xunius/era5-dl',
        packages=setuptools.find_packages(include=['era5dl', ]),
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Environment :: Console',
            'Intended Audience :: End Users/Desktop',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
            'Natural Language :: English',
            'Operating System :: POSIX :: Linux',
            'Operating System :: MacOS',
            'Operating System :: Microsoft',
            'Programming Language :: Python :: 3',
            'Topic :: Education'
            ],
        install_requires=[
            'cdsapi',
            ],
        python_requires='>=3',
        package_data={'era5dl': ['tables/*.csv', 'examples/*']},
        )

