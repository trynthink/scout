Maintenance
===========

.. _maint-philosophy:

Philosophy
----------

The development of Scout involved, as much as possible, the implementation of what were identified as "best practices," from the programming languages used to the formatting of the code. The language below outlines these practices.

* Use of open-source, well-established programming languages
* Avoiding deprecated or end-of-life languages or versions of languages
* Adherence to established code formatting guidelines and philosophies, when available (e.g., :pep:`8` and :pep:`20`)


.. _maint-vc:

Version Control with Git and GitHub
-----------------------------------

Scout relies on git for version control. 

Before Each Commit
~~~~~~~~~~~~~~~~~~

Making a commit in git should not be a source of heartburn, but there are several steps that should be taken to ensure each commit is high quality.

* Check all modified files for spelling errors (especially in the comment text)
* Check all modified files against appropriate linters (e.g., :pep:`8` and :pep:`257` for Python) or to make sure the file is syntactically valid (e.g., for JSON files)
* Check that the commit message itself is free of typos and spelling errors.
* Check to make sure that all tests are passing


.. _maint-documentation:

Documentation
-------------

The documentation for Scout is prepared using Sphinx, a package originally developed to document Python. Sphinx builds upon the reStructuredText markup language by adding a lot of handy features, like support for LaTeX equation markup with MathJax, automatic figure numbering, and simplified references to Python documentation. reStructuredText is a "semantic" markup language, and as a result, the documentation files have to be built to obtain their final, desired form. 

.. SUBSECTIONS TO ADD
.. useful reference documentation 
.. version numbering
.. handling the many 'residential' and 'commercial' links
.. toctree updates to add new sections
.. figure numbering :numfig:
.. the power (and complexity) of cross-referencing and auto-completion
.. the power of substitutions
.. custom configuration of extlinks
.. syntax specific settings and linters for rst/Sphinx (Sublime Text-specific)

.. FIGURE THIS OUT
.. documentation formatting rules and best practices
.. reference/citation formatting style
.. figure captions
.. 