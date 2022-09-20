easy-migration-tools
======================

Command line utilities for Data Station application management

SYNOPSIS
--------

```bash
pip3 install easy-migration-tools
update_thematische_collecties.py < OldThemCol.csv > NewThemCol.csv
list-bagstore-files [-p UUID | -d uuids.txt | -d - < uuids.txt] > files.csv 
```

DESCRIPTION
-----------

This module contains a variety of command line scripts to facilitate migration of datasets from EASY to a data-station.
Each script comes with a command line help.


INSTALLATION & CONFIGURATION
----------------------------

### Installation

* Globally:

  ```bash
  sudo pip3 install easy-migration-tools
  ```

* For the current user:

  ```bash
  pip3 install --user easy-migration-tools
  ```
  You may have to add the directory where `pip3` installs the command to the `PATH` manually.

### Configuration

The configuration file is called `.easy-migration-tools.yml`. Each command starts by looking for this file in the
current working directory and then in the user's home directory. If it is not found in either location it is
instantiated with some default and placeholder values in the current directory. It is recommended that you move this
file to your home directory. Using the configuration file from the current working directory is mainly useful for
development.

For the available configuration options and their meaning, see the explanatory comments in the configuration file
itself.
