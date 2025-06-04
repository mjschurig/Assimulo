#!/usr/bin/env python 
# -*- coding: utf-8 -*-

# Copyright (C) 2010-2023 Modelon AB  
#
# Alternative setup.py using pure setuptools (no Fortran extensions)
# This version only builds Cython/C extensions, not Fortran code

import logging
import sys 
import os
import shutil
import argparse
import warnings
from os.path import isfile, join
import numpy as np
from setuptools import setup, Extension, find_packages
import Cython
from Cython.Build import cythonize

def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")

# Simplified argument parsing for setuptools-only build
parser = argparse.ArgumentParser(description='Assimulo setup script (setuptools-only version).')
parser.register('type','bool',str2bool)
package_arguments=['plugins','sundials','blas','superlu','lapack','mkl']
package_arguments.sort()
for pg in package_arguments:
    parser.add_argument("--{}-home".format(pg), 
           help="Location of the {} directory".format(pg.upper()),type=str,default='')
parser.add_argument("--blas-name", help="name of the blas package",default='blas')
parser.add_argument("--extra-c-flags", help='Extra C-flags (a list enclosed in " ")',default='')
parser.add_argument("--with_openmp", type='bool', help="set to true if present",default=False)
parser.add_argument("--debug", type='bool', help="set to true if present",default=False)
parser.add_argument("--log",choices=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'),default='NOTSET')
parser.add_argument("--version", help='Package version number', default='Default')

args = parser.parse_known_args()
version_number_arg = args[0].version

logging.basicConfig(level=getattr(logging,args[0].log),format='%(levelname)s:%(message)s')

# Warning about Fortran extensions
warnings.warn(
    "This setuptools-only version does NOT build Fortran extensions (Hairer, ODEPACK, etc.). "
    "For full functionality, use the complete build system with numpy.distutils < 2.0 or "
    "migrate to scikit-build-core with CMake.",
    UserWarning
)

# Simplified build that only handles Cython extensions
def build_cython_extensions():
    """Build only the Cython/C extensions, skip Fortran code"""
    
    # Basic compiler flags
    extra_compile_args = ["-O2", "-fno-strict-aliasing"]
    extra_link_args = []
    
    if args[0].debug:
        extra_compile_args += ["-g"]
        extra_link_args += ["-g"]
    
    if args[0].extra_c_flags:
        extra_compile_args += args[0].extra_c_flags.split()
    
    if sys.platform == "darwin":
        extra_compile_args += ["-Wno-error=return-type"]
    
    if args[0].with_openmp:
        if 'win' in sys.platform:
            openmp_arg = "/openmp"
        else:
            openmp_arg = "-fopenmp"
        extra_compile_args.append(openmp_arg)
        extra_link_args.append(openmp_arg)
    
    # Determine include and library directories
    if args[0].sundials_home:
        incdirs = os.path.join(args[0].sundials_home, 'include')
        libdirs = os.path.join(args[0].sundials_home, 'lib')
    elif 'win' in sys.platform:
        incdirs = ''
        libdirs = ''
    else:
        incdirs = os.path.sep + os.path.join('usr', 'local', 'include')
        libdirs = os.path.sep + os.path.join('usr', 'local', 'lib')
    
    # Main modules
    ext_list = cythonize([
        "src/explicit_ode.pyx",
        "src/algebraic.pyx", 
        "src/implicit_ode.pyx",
        "src/ode.pyx",
        "src/problem.pyx",
        "src/special_systems.pyx",
        "src/support.pyx"
    ], 
    include_path=[".", "src"],
    force=True,
    compiler_directives={'language_level': "3str"})
    
    # Configure extensions
    for ext in ext_list:
        ext.include_dirs += [np.get_include(), "src"]
        ext.extra_compile_args += extra_compile_args
        ext.extra_link_args += extra_link_args
    
    # Explicit ODE needs additional source
    for ext in ext_list:
        if "explicit_ode" in ext.name:
            ext.sources += ["src/ode_event_locator.c"]
    
    # Euler solver
    euler_ext = cythonize(["src/solvers/euler.pyx"], 
                         include_path=[".", "src", "src/solvers"],
                         force=True,
                         compiler_directives={'language_level': "3str"})
    
    for ext in euler_ext:
        ext.include_dirs += [np.get_include(), "src"]
        ext.extra_compile_args += extra_compile_args
        ext.extra_link_args += extra_link_args
    
    ext_list.extend(euler_ext)
    
    # SUNDIALS (if available)
    if args[0].sundials_home and os.path.exists(os.path.join(incdirs, 'cvodes', 'cvodes.h')):
        logging.info("Building SUNDIALS extensions")
        
        sundials_ext = cythonize(["src/solvers/sundials.pyx"], 
                               include_path=[".", "src", "src/lib"],
                               force=True,
                               compiler_directives={'language_level': "3str"})
        
        sundials_ext[0].include_dirs += [np.get_include(), "src", "src/lib", incdirs]
        sundials_ext[0].library_dirs = [libdirs]
        sundials_ext[0].libraries = ["sundials_cvodes", "sundials_nvecserial", "sundials_idas"]
        sundials_ext[0].extra_compile_args += extra_compile_args
        sundials_ext[0].extra_link_args += extra_link_args
        
        kinsol_ext = cythonize(["src/solvers/kinsol.pyx"], 
                             include_path=[".", "src", "src/lib"],
                             force=True,
                             compiler_directives={'language_level': "3str"})
        
        kinsol_ext[0].include_dirs += [np.get_include(), "src", "src/lib", incdirs]
        kinsol_ext[0].library_dirs = [libdirs]
        kinsol_ext[0].libraries = ["sundials_kinsol", "sundials_nvecserial"]
        kinsol_ext[0].extra_compile_args += extra_compile_args
        kinsol_ext[0].extra_link_args += extra_link_args
        
        ext_list.extend(sundials_ext)
        ext_list.extend(kinsol_ext)
    else:
        logging.warning("SUNDIALS not found, skipping SUNDIALS extensions")
    
    return ext_list

# Build extensions
ext_modules = build_cython_extensions()

# Package metadata
NAME = "Assimulo"
AUTHOR = u"C. Winther (Andersson), C. Führer, J. Åkesson, M. Gäfvert"
AUTHOR_EMAIL = "christian.winther@modelon.com"
VERSION = "3.7.0.dev0" if version_number_arg == "Default" else version_number_arg
LICENSE = "LGPL"
URL = "http://www.jmodelica.org/assimulo"
DESCRIPTION = "A package for solving ordinary differential equations and differential algebraic equations."

LONG_DESCRIPTION = """
Assimulo is a Cython / Python based simulation package that allows for 
simulation of both ordinary differential equations (ODEs), f(t,y), and 
differential algebraic equations (DAEs), f(t,y,yd). 

This setuptools-only build provides core functionality but excludes 
Fortran-based solvers (Hairer, ODEPACK, etc.). For full functionality,
use the complete build with appropriate dependencies.
"""

setup(
    name=NAME,
    version=VERSION,
    license=LICENSE,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    platforms=["Linux", "Windows", "MacOS X"],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Cython',
        'Programming Language :: C',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: Unix'
    ],
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    ext_modules=ext_modules,
    python_requires=">=3.8",
    install_requires=[
        "numpy<2.0",
        "scipy", 
        "matplotlib",
        "Cython>=3.0"
    ],
    zip_safe=False,
) 