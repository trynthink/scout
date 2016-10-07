.. Substitutions
.. |cmd| unicode:: U+2318
.. |opt| unicode:: U+2325
.. |editor requirements| replace:: support for syntax-specific code coloring and syntax-specific formatting and there should be linting_ for Python and JSON built-in or available through add-on packages. Python code linting should include checking for compliance with `PEP 8`_ and pyflakes_, at a minimum

.. CONSIDER FIXING EXPLICIT PEP 8 REFERENCE BY MOVING PYTHON LINTING INFORMATION TO A MULTIPLY-REFERENCED FOOTNOTE

.. _PEP 8: https://www.python.org/dev/peps/pep-0008/
.. _pyflakes: https://pypi.python.org/pypi/pyflakes
.. _linting: https://en.wikipedia.org/wiki/Lint_(software)


.. _quick-start:

Setup Guide
===========

If you're new to Scout, this page is the right place to get started.

If you already have the :ref:`prerequisites <qs-prerequisites-list>` for Scout installed on your computer, move on to the :ref:`tutorials`.


.. _qs-setup:

Initial Setup
-------------

Before you can use Scout, you'll need to install a few things that Scout relies upon to run. Preparing for and using Scout requires interacting a bit with the command line, but these instructions will walk through each step in the set up process with the specific commands required. While the basic prerequisites are the same for :ref:`Mac <qs-mac>` and :ref:`Windows <qs-windows>` users, because the details and order of the steps are somewhat different, separate instructions are provided. Before beginning, you'll need to be using a computer where you have administrator-level privileges so that you can install new software.

If you're comfortable at the command line, install or set up everything in this list of prerequisites and then skip straight to the :ref:`tutorials`.

.. _qs-prerequisites-list:

**Prerequisites**

* R
* Python 3
* Python packages: pip [#]_, numpy
* A text editor of your choice

The installation instructions for :ref:`Mac <qs-mac>` and :ref:`Windows <qs-windows>` assume that none of these prerequisite programs or distributions are installed on your system. Please follow the instructions as appropriate, given what might already installed on your system and checking for updates if appropriate.

.. warning::
   Please use due care and take appropriate security precautions to ensure that your system is not compromised when installing the programs and distributions identified below. It is your responsibility to protect the integrity of your system. *Caveat utilitor.*


.. _qs-mac:

Mac OS
------

0. (Optional) Install a package manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Mac OS ships with Python already installed. Installing and using a package manager will make it easy to ensure that any additional installations of Python do not interfere with the version of Python included with the operating system. Homebrew_ is a popular package manager, but there are other options, such as MacPorts and Fink.

.. _Homebrew website:
.. _Homebrew: http://brew.sh

.. note::
   While this step is optional, subsequent instructions are written with the assumption that you have installed Homebrew as your package manager.

To install Homebrew, open Terminal (found in Applications > Utilities, or trigger Spotlight with |cmd|-space and type "Terminal"). Visit the `Homebrew website`_ and copy the installation command text on the page. Paste the text into the Terminal application window and press Return. If you encounter problems with the installation, return to the Homebrew website for help or search online for troubleshooting assistance.

If you are using a package manager other than Homebrew, follow the documentation for that package manager to install Python 3. If you have chosen to not install a package manager, you may use the `Python Software Foundation installer`_ for the latest version of Python 3.

.. _Python Software Foundation installer: https://www.python.org/downloads/

1. Install Python 3
~~~~~~~~~~~~~~~~~~~

In a Terminal window, at the command prompt (a line terminated with a $ character and a flashing cursor), type::

   brew install python3

2. Install required Python packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once Python 3 is fully installed, pip3 is the tool you will use to install add-ons specific to Python 3. Only one package, numpy, is absolutely mandatory for Scout. To install it, at the command prompt in Terminal, type::

   pip3 install numpy

.. CONSIDER ADDING INSTRUCTIONS TO VERIFY THAT NUMPY WAS SUCCESSFULLY INSTALLED BY OPENING PYTHON AND IMPORTING NUMPY

.. _qs-mac-text-editor:

3. Install a text editor
~~~~~~~~~~~~~~~~~~~~~~~~

A third-party text editor will make it easier to change Scout files. There are `many different text editors`_ available for the Mac. Mac OS X ships with two command line interface editors, vim and emacs. You may use one of these or install and use another graphical or command line interface editor of your choice. Whatever editor you choose should have |editor requirements|.

.. _many different text editors: https://en.wikipedia.org/wiki/Comparison_of_text_editors

`Sublime Text`_ is an easy to use text editor with a graphical interface that can be configured to satisfy the specified requirements. To set up Sublime Text for working with Scout, `download Sublime Text 3`_, open the downloaded disk image, and drag the application file to the Applications folder using the shortcut provided.

.. _Sublime Text: http://www.sublimetext.com
.. _download Sublime Text 3: http://www.sublimetext.com/3

After installing Sublime Text, there are several additional configuration steps that will help get the editor ready for viewing and editing Python and JSON files.

First, open Sublime Text and, following the directions_ provided by the developer, install Package Control.

.. _directions: https://packagecontrol.io/installation

We will use Package Control to install the additional features needed for checking Python files. To access Package Control, open the Command Palette (Tools > Command Palette or |cmd|\ |opt|\ P) and then begin typing "Package Control: Install Package." Click that option once it appears in the list or use the arrow keys to navigate up and down the list that appears and press the return key when the "Install Package" function for Package Control is highlighted in the list. In the search field that appears, begin typing "SublimeLinter" and click the package when it appears in the list to install the package.

Before proceeding further, open a Terminal window and at the command prompt, use pip3 to install the pep8 and pyflakes packages::

   pip3 install pep8
   pip3 install pyflakes

Once both pep8 and pyflakes have been installed successfully, return to Sublime Text. Open Package Control to install new packages following the same steps. Install the "SublimeLinter-pep8," "SublimeLinter-json," and "SublimeLinter-pyflakes" packages.

Finally, the Python-specific settings for Sublime Text need to be updated. Open a new file in Sublime Text and save it with the file name "asdf.py." Open the Python syntax-specific settings (Sublime Text > Preferences > Settings – Syntax Specific) and between the braces, paste::

   "spell_check": true,
   "tab_size": 4,
   "translate_tabs_to_spaces": true,
   "rulers": [80]

Save the modified file and close the window. Once complete, delete "asdf.py."

Quit and reopen Sublime Text to apply all of the settings changes and new packages that have been installed.

.. Atom instructions, in case they ever become useful, are commented out below.

.. Open the zipped file downloaded from the Atom_ website and drag the Atom application to the Applications folder. 

.. Once Atom is installed, you must add the packages that check Python and JSON files for integrity. Open the Settings (Atom > Preferences), which will open a new tab in your Atom window. In the left sidebar in the newly opened Settings tab, click "Install." Type "linter-pep8" into the search field on the Install page and hit return (make sure "Packages" is selected as the search option). Identify the correct package ("linter-pep8") in the list of search results and click the appropriate "Install" button. Once complete, search again for "linter-jsonlint" and complete the installation.


4. Install R
~~~~~~~~~~~~

Download the installer package for the latest version of R (or the version appropriate for the version of the Mac OS on your system) from the `R for Mac OS X page`_ on the CRAN website.

.. _R for Mac OS X page: https://cran.r-project.org/bin/macosx/

Follow the instructions in the installer to complete the installation.


.. _qs-windows:

Windows
-------

.. warning::
   These instructions have not been tested. Unforeseen problems might be encountered as a result of missing steps in these directions.

1. Install Python 3
~~~~~~~~~~~~~~~~~~~

Download the executable installer for Windows available on the Python Software Foundation `downloads page`_. Run the installer and follow the on-screen prompts as you would with any other software installer. At the relevant step in the installation process, ensure that the option is selected to update or adjust the system PATH environment variable.

.. _downloads page: https://www.python.org/downloads/

.. note::
   Two download buttons might appear near the top of the page. Be sure to choose the appropriate option for Python 3, not Python 2.

2. Install required Python packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once Python 3 installation is complete, the numpy package needs to be installed. Begin by `opening a command prompt`_ window. At the prompt (a line of text with a file path terminated by a greater than symbol, such as ``C:\>``), type::

   py -3 -m pip install numpy

.. _opening a command prompt: http://www.digitalcitizen.life/7-ways-launch-command-prompt-windows-7-windows-8

3. Install a text editor
~~~~~~~~~~~~~~~~~~~~~~~~

While Windows comes with a plain text editor, Notepad, there are `many different text editors`_ available for Windows that will make it much easier to view and change Scout files. You are welcome to use the editor of your choice, but whatever you choose should have |editor requirements|.

Sublime Text is an easy to use cross-platform text editor that can be configured to have the necessary features for authoring Python and JSON files. The instructions are the same as those :ref:`provided for Mac users <qs-mac-text-editor>`, but the shortcut key commands and the process for installing pep8 and pyflakes will be different in Windows. Follow the instructions already outlined for installing Python packages using pip to install pep8 and pyflakes.

4. Install R
~~~~~~~~~~~~

Download R from CRAN_ and run the executable, again following the instructions in the installer. The downloads page includes links to pages with additional details regarding installation and the configuration of R specific to Windows.

.. _CRAN: https://cran.r-project.org/bin/windows/base/release.htm


.. rubric:: Footnotes
.. [#] pip/pip3 is typically installed at the same time that Python 3 is installed.