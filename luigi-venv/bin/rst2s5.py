#!/Users/christianmueller/Library/Mobile Documents/com~apple~CloudDocs/Studies/Academic/5. MSc CS/2022/2022.1/7. DLMDSEDE02 Project Data Engineering/4. Assignments/Deliverables/DLMDSEDE02-project-cmueller/luigi-venv/bin/python3

# $Id: rst2s5.py 4564 2006-05-21 20:44:42Z wiemann $
# Author: Chris Liechti <cliechti@gmx.net>
# Copyright: This module has been placed in the public domain.

"""
A minimal front end to the Docutils Publisher, producing HTML slides using
the S5 template system.
"""

try:
    import locale
    locale.setlocale(locale.LC_ALL, '')
except:
    pass

from docutils.core import publish_cmdline, default_description


description = ('Generates S5 (X)HTML slideshow documents from standalone '
               'reStructuredText sources.  ' + default_description)

publish_cmdline(writer_name='s5', description=description)
