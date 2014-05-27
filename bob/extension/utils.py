#!/usr/bin/env python
# encoding: utf-8
# Andre Anjos <andre.dos.anjos@gmail.com>
# Fri 21 Mar 2014 10:37:40 CET

'''General utilities for building extensions'''

import os
import re
import sys
import glob
import platform

DEFAULT_PREFIXES = [
    "/usr",
    "/usr/local",
    "/opt/local",
    ]

def find_file(name, subpaths=None, prefixes=None):
  """Finds a generic file on the file system. Returns all candidates.

  This method will find all occurrences of a given name on the file system and
  will return them to the user.

  If the environment variable ``BOB_PREFIX_PATH`` is set, then it is
  considered a unix path list that is prepended to the list of prefixes to
  search for. The environment variable has the highest priority on the search
  order. The order on the variable for each path is respected.

  Parameters:

  name, str
    The name of the file to be found, including extension

  subpaths, str list
    A list of subpaths to be appended to each prefix for the search. For
    example, if you specificy ``['foo', 'bar']`` for this parameter, then
    search on ``os.path.join(prefixes[0], 'foo')``, ``os.path.join(prefixes[0],
    'bar')``, and so on. Globs are accepted in this list and resolved using
    the function :py:func:`glob.glob`.

  prefixes, str list
    A list of prefixes that will be searched prioritarily to the
    ``DEFAULT_PREFIXES`` defined in this module.

  Returns a list of filenames that exist on the filesystem, matching your
  description.
  """

  search = []

  # Priority 1
  if 'BOB_PREFIX_PATH' in os.environ:
    search += os.environ['BOB_PREFIX_PATH'].split(os.pathsep)

  # Priority 2
  if prefixes:
    search += prefixes

  # Priority 3
  search += DEFAULT_PREFIXES

  # Make unique to avoid searching twice
  search = uniq(search)

  # Exhaustive combination of paths and subpaths
  if subpaths:
    subsearch = []
    for s in search:
      for p in subpaths:
        subsearch.append(os.path.join(s, p))
      subsearch.append(s)
    search = subsearch

  # Before we do a filesystem check, filter out the unexisting paths
  tmp = []
  for k in search: tmp += glob.glob(k)
  search = tmp

  retval = []
  candidates = []
  for path in search:
    candidate = os.path.join(path, name)
    candidates.append(candidate)
    if os.path.exists(candidate): retval.append(candidate)

  return retval

def find_header(name, subpaths=None, prefixes=None):
  """Finds a header file on the file system. Returns all candidates.

  This method will find all occurrences of a given name on the file system and
  will return them to the user.

  If the environment variable ``BOB_PREFIX_PATH`` is set, then it is
  considered a unix path list that is prepended to the list of prefixes to
  search for. The environment variable has the highest priority on the search
  order. The order on the variable for each path is respected.

  Parameters:

  name, str
    The name of the file to be found, including extension

  subpaths, str list
    A list of subpaths to be appended to each prefix for the search. For
    example, if you specificy ``['foo', 'bar']`` for this parameter, then
    search on ``os.path.join(prefixes[0], 'foo')``, ``os.path.join(prefixes[0],
    'bar')``, and so on.

  prefixes, str list
    A list of prefixes that will be searched prioritarily to the
    ``DEFAULT_PREFIXES`` defined in this module.

  Returns a list of filenames that exist on the filesystem, matching your
  description.
  """

  # Exhaustive combination of paths and subpaths
  if subpaths:
    my_subpaths = [os.path.join('include', k) for k in subpaths]
  else:
    my_subpaths = ['include']

  return find_file(name, my_subpaths, prefixes)

def find_library(name, version=None, subpaths=None, prefixes=None,
    only_static=False):
  """Finds a library file on the file system. Returns all candidates.

  This method will find all occurrences of a given name on the file system and
  will return them to the user.

  If the environment variable ``BOB_PREFIX_PATH`` is set, then it is
  considered a unix path list that is prepended to the list of prefixes to
  search for. The environment variable has the highest priority on the search
  order. The order on the variable for each path is respected.

  Parameters:

  name, str
    The name of the module to be found. If you'd like to find libz.so, for
    example, specify ``"z"``. For libmath.so, specify ``"math"``.

  version, str
    The version of the library we are searching for. If not specified, then
    look only for the default names, such as ``libz.so`` and the such.

  subpaths, str list
    A list of subpaths to be appended to each prefix for the search. For
    example, if you specificy ``['foo', 'bar']`` for this parameter, then
    search on ``os.path.join(prefixes[0], 'foo')``, ``os.path.join(prefixes[0],
    'bar')``, and so on.

  prefixes, str list
    A list of prefixes that will be searched prioritarily to the
    ``DEFAULT_PREFIXES`` defined in this module.

    static (bool)
      A boolean, indicating if we should try only to search for static versions
      of the libraries. If not set, any would do.

  Returns a list of filenames that exist on the filesystem, matching your
  description.
  """

  libpaths = ['lib']

  if platform.architecture()[0] == '32bit':
    libpaths += [
        os.path.join('lib', 'i386-linux-gnu'),
        os.path.join('lib32'),
        ]
  else:
    libpaths += [
        os.path.join('lib', 'x86_64-linux-gnu'),
        os.path.join('lib64'),
        ]

  # Exhaustive combination of paths and subpaths
  if subpaths:
    my_subpaths = []
    for lp in libpaths:
      my_subpaths += [os.path.join(lp, k) for k in subpaths]
  else:
    my_subpaths = libpaths

  # Extensions to consider
  if only_static:
    extensions = ['.a']
  else:
    if sys.platform == 'darwin':
      extensions = ['.dylib', '.a']
    elif sys.platform == 'win32':
      extensions = ['.dll', '.a']
    else: # linux like
      extensions = ['.so', '.a']

  # The module names can be set with or without version number
  retval = []
  if version:
    for ext in extensions:
      if sys.platform == 'darwin': # version in the middle
        libname = 'lib' + name + '.' + version + ext
      else: # version at the end
        libname = 'lib' + name + ext + '.' + version

      retval += find_file(libname, my_subpaths, prefixes)

  for ext in extensions:
    libname = 'lib' + name + ext
    retval += find_file(libname, my_subpaths, prefixes)

  return retval

def uniq(seq):
  """Uniqu-fy preserving order"""

  seen = set()
  seen_add = seen.add
  return [x for x in seq if x not in seen and not seen_add(x)]

def egrep(filename, expression):
  """Runs grep for a given expression on each line of the file

  Parameters:

  filename, str
    The name of the file to grep for the expression

  expression
    A regular expression, that will be initialized using :py:func:`re.compile`.

  Returns a list of re matches.
  """

  retval = []

  with open(filename, 'rt') as f:
    rexp = re.compile(expression)
    for line in f:
      p = rexp.match(line)
      if p: retval.append(p)

  return retval