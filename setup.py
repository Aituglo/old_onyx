

import sys

from setuptools import setup , find_packages


setup(name="onyxproject",
      description="Intelligent Dashboard",
      version='0.8.8',
      include_package_data=True,
      packages=['onyx'],
      url="https://github.com/OnyxProject/Onyx",
      maintainer=("Aituglo"),
      maintainer_email="ckhouani@live.fr",
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Environment :: Web Environment",
          "Intended Audience :: Developers",
          "Intended Audience :: System Administrators",
          "Operating System :: OS Independent",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.5",
          "Topic :: Software Development :: Build Tools",
          "Topic :: System :: Software Distribution"],
      zip_safe=True,
      entry_points={
          'console_scripts': [
                'onyxclient=onyx.main:run',
                'onyxvoice=onyx.client.speech.main:run'
                ]
      },
      install_requires=[
        'pip',
        'pytz',
        'Babel',
        'jsonify',
        'pytest',
        'colorlog',
        'aiml',
        'uptime',
        'onyxbabel',
        'flask-apidoc',
        'configparser',
        'psutil',
        'Flask-Script',
        'pylibmc',
        'Flask-restplus',
        'Flask-FlatPages',
        'Markdown',
        'PyYAML',
        'Werkzeug',
        'flask-migrate',
        'itsdangerous',
        'speaklater',
        'Flask-Cache',
        'pylibmc',
        'redis',
        'celery',
        'gitpython',
        'flask-restless',
        'Flask==0.10.1',
        'Flask-WTF',
        'onyx_sqlalchemy',
        'requests',
        'beautifulsoup4',
        'Flask-Menu',
        'Flask-Login',
        'SQLAlchemy-migrate',
        'flask_bcrypt',
        'flask-Mail',
        'blinker',
        'wikipedia',
        'markupsafe',
        'pyaudio',
        'SpeechRecognition',
        'gtts'
        ],
      options={
          'bdist_wheel': {'universal': True},
      },
      platforms=['any'],
      )
