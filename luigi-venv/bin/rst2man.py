#!/Users/christianmueller/Library/Mobile Documents/com~apple~CloudDocs/Studies/Academic/5. MSc CS/2022/2022.1/7. DLMDSEDE02 Project Data Engineering/4. Assignments/Deliverables/DLMDSEDE02-project-cmueller/luigi-venv/bin/python3

# Author:
# Contact: grubert@users.sf.net
# Copyright: This module has been placed in the public domain.

"""
man.py
======

This module provides a simple command line interface that uses the
man page writer to output from ReStructuredText source.
"""

import locale
try:
    locale.setlocale(locale.LC_ALL, '')
except:
    pass

from docutils.core import publish_cmdline, default_description
from docutils.writers import manpage

description = ("Generates plain unix manual documents.  " + default_description)

publish_cmdline(writer=manpage.Writer(), description=description)
