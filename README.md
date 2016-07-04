[![Circle CI](https://circleci.com/gh/cloudify-cosmo/get-cloudify.py/tree/master.svg?style=shield)](https://circleci.com/gh/cloudify-cosmo/get-cloudify.py/tree/master)
[![Build status](https://ci.appveyor.com/api/projects/status/rua8r22tsvvl05lt/branch/master?svg=true)](https://ci.appveyor.com/project/Cloudify/get-cloudify.py/branch/master)

This scripts installs Cloudify's CLI (http://github.com/cloudify-cosmo/cloudify-cli).

It currently supports Windows (32 and 64 bit), OSX, Debian/RHEL based distributions and Arch.
It requires Python 2.7.x to run. Other than that, it will attempt to install all other requirements for you.

Download manually or:

```bash
curl -O http://gigaspaces-repository-eu.s3.amazonaws.com/org/cloudify3/get-cloudify.py
# or
wget http://gigaspaces-repository-eu.s3.amazonaws.com/org/cloudify3/get-cloudify.py
```

and run:

```bash
python get-cloudify.py -h
```


By default, the script will not install any prerequisites (such as pip, virtualenv, python-dev/devel, etc..) unless explicitly specified. It's important to read the help to understand what the script can do.
