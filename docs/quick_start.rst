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

Initial setup
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

To install Homebrew, open Terminal (found in Applications/Utilities, or trigger Spotlight with |cmd|-space and type "Terminal"). Visit the `Homebrew website`_ and copy the installation command text on the page. Paste the text into the Terminal application window and press Return. If you encounter problems with the installation, return to the Homebrew website for help or search online for troubleshooting assistance.

If you are using a package manager other than Homebrew, follow the documentation for that package manager to install Python 3. If you have chosen to not install a package manager, you may use the `Python Software Foundation installer`_ for the latest version of Python 3.

.. _Python Software Foundation installer: https://www.python.org/downloads/

1. Install Python 3
~~~~~~~~~~~~~~~~~~~

In a Terminal window, at the command prompt (a line terminated with a $ character and a flashing cursor), type::

   brew install python3

2. Install required Python packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once Python 3 is fully installed, pip3 is the tool you will use to install add-ons specific to Python 3. Only one package, numpy, is required for Scout. To install it, at the command prompt in Terminal, type::

   pip3 install numpy

If you'd like to confirm that numpy was installed successfully, you can start Python from the command prompt in Terminal by typing::

   python3

and import numpy (within the Python interactive shell, indicated by the ``>>>`` prompt). :: 

   import numpy

If no error or warning messages appear, then the installation was successful and you can exit Python by typing ``quit()``.

3. Install a text editor
~~~~~~~~~~~~~~~~~~~~~~~~

A third-party text editor will make it easier to change Scout files. There are `many different text editors`_ available for the Mac. Mac OS X ships with two command line interface editors, vim and emacs. You may use one of these or install and use another graphical or command line interface editor of your choice. Whatever editor you choose should have |editor requirements|.

.. _many different text editors: https://en.wikipedia.org/wiki/Comparison_of_text_editors

For the purposes of this documentation, the following instructions will step through how to install `Sublime Text`_, an easy to use text editor with a graphical interface that can be configured to satisfy the specified requirements. These instructions are provided to illustrate the steps required to configure a text editor for viewing and modifying Python and JSON files and should not be construed as an endorsement or promotion of Sublime Text.

.. _Sublime Text: http://www.sublimetext.com

1. Download Sublime Text
************************

To set up Sublime Text for working with Scout, `download Sublime Text 3`_, open the downloaded disk image, and drag the application file to the Applications folder using the shortcut provided.

.. _download Sublime Text 3: http://www.sublimetext.com/3

After installing Sublime Text, there are several additional configuration steps that will help get the editor ready for viewing and editing Python and JSON files.

2. Install Package Control
**************************

First, open Sublime Text and, following the directions_ provided by the developer, install Package Control.

.. _directions: https://packagecontrol.io/installation

Once installed, Package Control is opened via the Command Palette (Tools > Command Palette or |cmd|\ |opt|\ P). Begin typing "Package Control" into the Command Palette. If a list of options beginning with "Package Control" appear, then the installation was successful. If not, refer back to the `Package Control website`_ for troubleshooting help.

.. _Package Control website: https://packagecontrol.io/docs

We will use Package Control to install the additional features needed for checking Python files. 

3. Install SublimeLinter prerequisites
**************************************

Before proceeding further, open a Terminal window and at the command prompt, use pip3 to install the pep8 and pyflakes packages::

   pip3 install pep8
   pip3 install pyflakes

4. Install SublimeLinter
************************

Return to Sublime Text and open Package Control using the Command Palette (Tools > Command Palette or |cmd|\ |opt|\ P). Begin typing "Package Control: Install Package" in the Command Palette and click that option once it appears in the list. (Arrow keys can also be used to move up and down in the list.) In the search field that appears, begin typing "SublimeLinter" and click the package when it appears in the list to install the package. If installation was successful for this (or any other) package, the package name will appear in Preferences > Package Settings.

5. Install specific code linters
********************************

Open the Command Palette and select "Package Control: Install Package" again to install new packages following the same steps. Install the "SublimeLinter-pep8," "SublimeLinter-json," and "SublimeLinter-pyflakes" packages.

6. Configure Python syntax-specific preferences
***********************************************

Finally, the Python-specific settings for Sublime Text need to be updated. Open a new file in Sublime Text and save it with the file name |html-filepath| asdf.py\ |html-fp-end|. (|html-filepath|\ asdf.py |html-fp-end| will be deleted later.) Open the Python syntax-specific settings (Sublime Text > Preferences > Settings – Syntax Specific) and between the braces, paste::

   "spell_check": true,
   "tab_size": 4,
   "translate_tabs_to_spaces": true,
   "rulers": [80]

Save the modified file and close the window. Once complete, delete |html-filepath| asdf.py\ |html-fp-end|.

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

0. Determine whether you have 32-bit or 64-bit Windows installed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some of the software prerequisites for Scout have different versions for 32-bit and 64-bit installations of Windows. If you are unsure of whether your computer is running 32-bit or 64-bit Windows, you can follow `these instructions`_ from Microsoft to find out.

.. _these instructions: https://support.microsoft.com/en-us/help/827218/how-to-determine-whether-a-computer-is-running-a-32-bit-version-or-64-bit-version-of-the-windows-operating-system

1. Install Python 3
~~~~~~~~~~~~~~~~~~~

.. tip::
   If you have 64-bit Windows installed on your computer, downloading and installing the 64-bit version of Python is recommended. 

Download the executable installer for Windows available on the Python Software Foundation `downloads page`_. Run the installer and follow the on-screen prompts as you would with any other software installer. Be sure that the option in the installer "Add Python 3.x to PATH," where x denotes the current version of Python 3, is checked.

.. _downloads page: https://www.python.org/downloads/

.. note::
   Two download buttons might appear near the top of the page. Be sure to choose the appropriate option for Python 3, not Python 2.

2. Install required Python packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once Python 3 installation is complete, the numpy package needs to be installed. pip is the tool you will use to install add-ons specific to Python 3. Begin by `opening a command prompt`_ window. At the prompt (a line of text with a file path terminated by a greater than symbol, such as ``C:\>``), type::

   py -3 -m pip install numpy

.. _Open a command prompt:
.. _opening a command prompt: http://www.digitalcitizen.life/7-ways-launch-command-prompt-windows-7-windows-8

If you would like to confirm that numpy was installed successfully, you can open an interactive session of Python in a command prompt window by typing::

   py -3

and then importing numpy (within the Python interactive session, indicated by a ``>>>`` prompt)::

   import numpy

If no error or warning messages appear, numpy was installed successfully. Exit the interactive session of Python by typing::

   quit()

3. Install a text editor
~~~~~~~~~~~~~~~~~~~~~~~~

While Windows comes with a plain text editor, Notepad, there are `many different text editors`_ available for Windows that will make it much easier to view and change Scout files. You are welcome to use the editor of your choice, but whatever you choose should have |editor requirements|.

`Sublime Text`_ is an easy to use cross-platform text editor that can be configured to have the necessary features for authoring Python and JSON files. The following instructions are provided to illustrate the steps required to configure a text editor for viewing and modifying Python and JSON files and should not be construed as an endorsement or promotion of Sublime Text.

1. Install Sublime Text
***********************

To set up Sublime Text for working with Scout, `download Sublime Text 3`_ and run the installer. The installer will automatically place the application and supporting files in the appropriate locations on your system.

After installing Sublime Text, there are several additional configuration steps that will help get the editor ready for viewing and editing Python and JSON files.

2. Install Package Control
**************************

First, open Sublime Text and, following the directions_ provided by the developer, install Package Control.

.. _directions: https://packagecontrol.io/installation

Once installed, Package Control is opened via the Command Palette (Tools > Command Palette or Ctrl+Shift+P). Begin typing "Package Control" into the Command Palette. If a list of options beginning with "Package Control" appear, then the installation was successful. If not, refer back to the `Package Control website`_ for troubleshooting help.

.. _Package Control website: https://packagecontrol.io/docs

We will use Package Control to install the additional features needed for checking Python files. 

3. Install SublimeLinter prerequisites
**************************************

Before proceeding further, `open a command prompt`_ window and type the following commands to use pip to install the pep8 and pyflakes packages::

   py -3 -m pip install pep8
   py -3 -m pip install pyflakes

Once you have 

4. Install SublimeLinter
************************

Return to Sublime Text and open Package Control using the Command Palette (Tools > Command Palette or Ctrl+Shift+P). Begin typing "Package Control: Install Package" in the Command Palette and click that option once it appears in the list. (Arrow keys can also be used to move up and down in the list.) In the search field that appears, begin typing "SublimeLinter" and click the package name when it appears in the list to install the package. If installation was successful for this (or any other) package, the package name will appear in Preferences > Package Settings.

5. Install specific code linters
********************************

Open the Command Palette and select "Package Control: Install Package" again to install new packages following the same steps. Install the "SublimeLinter-pep8," "SublimeLinter-json," and "SublimeLinter-pyflakes" packages.

6. Configure Python syntax-specific preferences
***********************************************

Finally, the Python-specific settings for Sublime Text need to be updated. Open a new file in Sublime Text and save it with the file name |html-filepath| asdf.py\ |html-fp-end|. (|html-filepath|\ asdf.py |html-fp-end| will be deleted later.) Open the Python syntax-specific settings (Preferences > Settings – Syntax Specific) and between the braces, paste::

   "spell_check": true,
   "tab_size": 4,
   "translate_tabs_to_spaces": true,
   "rulers": [80]

Save the modified file and close the window, then delete |html-filepath| asdf.py\ |html-fp-end|.

Quit and reopen Sublime Text to apply all of the settings changes and new packages that have been installed.

4. Install R
~~~~~~~~~~~~

Download R from CRAN_ and run the executable, again following the instructions in the installer. The downloads page includes links to pages with additional details regarding installation and the configuration of R specific to Windows. In particular, the `R FAQ explains`_ whether you should use the 32-bit or 64-bit version of R. After running the R installer, no further configuration of R is required for this initial setup.

.. _CRAN: https://cloud.r-project.org/bin/windows/base/
.. _R FAQ explains: https://cloud.r-project.org/bin/windows/base/rw-FAQ.html#Should-I-run-32_002dbit-or-64_002dbit-R_003f

5. Install Perl
~~~~~~~~~~~~~~~

1. Verify status of Perl installation
*************************************

Before installing Perl, confirm that it is not already installed on your system. `Open a command prompt`_ window and at the prompt, type::

   perl -v

If you get a response that begins with ``'perl' is not recognized``, Perl is not installed on your system and you should continue to the next step. If you get a response that includes a version number for Perl, you have a valid Perl installation on your system and no further configuration of your system is required before moving on to the :ref:`tutorials`.

2. Download and install Perl
****************************

From the `Strawberry Perl website`_, download the "recommended version" that is appropriate for your system configuration, either 32- or 64-bit. Open the Strawberry Perl installer and follow the instructions to complete the installation of Perl.

.. _Strawberry Perl website: http://strawberryperl.com

No further steps are required to set up Perl. If you would like to verify that the installation was successful, close any currently open command prompt windows, open a new command prompt and type ``perl -v`` again. The response should indicate that a version of Perl is now installed. If not, visit the `Strawberry Perl support page`_ for additional resources.

.. _Strawberry Perl support page: http://strawberryperl.com/support.html

3. (Optional) Verify Perl installation in R
*******************************************

Perl is required for one of the packages that Scout uses in R. If you would like, you can verify that your Perl installation is recognized in R. To begin, open R (sometimes called R GUI) from the Start Menu. In the R console window that opens, at the prompt (indicated by a ">" character), type::

   install.packages("WriteXLS")

You will be prompted to select a "CRAN mirror," which is the server from which you will download the "WriteXLS" package. Once the installation is complete, at the R prompt, type::

   library("WriteXLS")
   testPerl()

If your Perl installation is successfully recognized by R, the messages "Perl found." and "All required Perl modules were found." will print to the R console window. 
   

.. rubric:: Footnotes
.. [#] pip/pip3 is typically installed at the same time that Python 3 is installed.