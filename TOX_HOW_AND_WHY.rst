=================================
What is Tox? And How to Use It?
=================================

Tox is a generic virtualenv management and test command-line tool.

It's used to check that your package installs correctly with different Python versions and interpreters, and to run your tests in each of the environments.

Here's a breakdown of our ``tox.ini`` to explain how we utilize Tox in this project.

tox.ini Explained
=================

.. code-block:: ini

    [tox]
    requires =
        tox>=4.2
    env_list =

    [testenv:migrations]
    base_python = python3.10
    setenv =
        PYTHONPATH = {toxinidir}/src:{toxinidir}
    deps =
        Django==4.2
        -rrequirements.txt
    commands =
        python tests/migration_script.py

Sections
--------

- ``[tox]``: General Tox settings. Requires Tox version 4.2 or higher.
- ``env_list``: Environments that Tox will run.

- ``[testenv:migrations]``: Custom test environment for generating Django migrations in ``tests`` directory.
  - ``setenv``: Sets environment variables.
  - ``deps``: Lists the dependencies required for this test environment.
  - ``commands``: Commands that Tox will run in this environment.

How to Run Tox
==============

1. First, install Tox if you haven't already::

    pip install tox

2. To run all the environments specified in ``env_list``::

    tox

3. To run the migrations::

    tox -e migrations
