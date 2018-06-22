# version.py
# contains version information
# usage:
# from version import version as __version__

__version_info = (0,0,2)
__version__ = '.'.join(map(str, __version_info))

version = __version__
