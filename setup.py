#!/usr/bin/env python

from distutils.core import setup, Extension
import numpy

#build using python setup.py build --build-platlib=.

setup(name="cplasma", version="1.0",
      ext_modules=[
          Extension("led/effects/cplasma", ["led/effects/cplasma/cplasma.c"],
              extra_compile_args=['-Os', '-funroll-loops', '-ffast-math'],
          ),
      ],
      include_dirs = [numpy.get_include()],
)

