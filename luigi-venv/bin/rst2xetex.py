#!/Users/christianmueller/Library/Mobile Documents/com~apple~CloudDocs/Studies/Academic/5. MSc CS/2022/2022.1/7. DLMDSEDE02 Project Data Engineering/4. Assignments/Deliverables/DLMDSEDE02-project-cmueller/luigi-venv/bin/python3

# $Id: rst2xetex.py 7847 2015-03-17 17:30:47Z milde $
# Author: Guenter Milde
# Copyright: This module has been placed in the public domain.

"""
A minimal front end to the Docutils Publisher, producing Lua/XeLaTeX code.
"""

try:
    import locale
    locale.setlocale(locale.LC_ALL, '')
except:
    pass

from docutils.core import publish_cmdline

description = ('Generates LaTeX documents from standalone reStructuredText '
               'sources for compilation with the Unicode-aware TeX variants '
               'XeLaTeX or LuaLaTeX. '
               'Reads from <source> (default is stdin) and writes to '
               '<destination> (default is stdout).  See '
               '<http://docutils.sourceforge.net/docs/user/latex.html> for '
               'the full reference.')

publish_cmdline(writer_name='xetex', description=description)
