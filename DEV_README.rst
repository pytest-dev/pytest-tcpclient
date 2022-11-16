Development
-----------

If you want to use a virtual environment, do that first and activate it. You
can use any virtual environment system you like. However, if you want to use
``virtualenv`` (and you already have ``virtualenv`` installed) you could do this:

.. code-block:: sh

   $ virtualenv -p3.8 venv

Next, make the project:

.. code-block:: sh

    $ make

That will do the following:

- Install all the dependencies
- Run the tests
- Generate a coverage report
- Fail if the coverage is below 100%

Build configuration
+++++++++++++++++++

Build configuration is mostly stored in ``pyproject.toml``. Idealy, it would all be in
there. However, there are two exceptions.

First, ``setuptools`` has been chosen as the build system. Unfortunately, to install
``pytest-tcpclient`` in editable mode, a minimial ``setup.py`` must be and has been provided.

Packages that ``pytest-tcpclient`` requires to run are listed in ``pyproject.toml``.

Packages required for development (testing, coverage and linting) are listed in
``dev_dependencies.txt``.

``tox`` has been configured (in ``tox.ini``) to install those packages before running
the tests.

``setuptools`` has been configured to supply the option ``dev`` for those extra packages.
For example, the ``Makefile`` has the following command to initialise the virtual
environment:

.. code-block:: sh

    $ python -m pip install -e .[dev]

Default ``make`` target is ``style_and_test``
+++++++++++++++++++++++++++++++++++++++++++++

The default target in the ``Makfile`` is ``style_and_test`` which first calls
the linter, then runs the tests and, finally, checks that code coverage is 100%

``tox``
+++++++

``tox`` is only used for CI builds. See ``.github/workflows/build.yml``.

``make`` detects changes to configuration files
+++++++++++++++++++++++++++++++++++++++++++++++

If any of the build system configuration files, ``make`` will reinstall all dependencies.

Continuous Integration and Deployment
+++++++++++++++++++++++++++++++++++++

There is a workflow (``.github/workflows/build.yml``) that will build and test pull
requests with ``tox``.

There is another workflow (``.github/workflows/publish.yml``) that is triggered
by the appearance of new version tags on the ``main`` branch. It will
build and test the code and additionally publish the package to
``pypi``.
