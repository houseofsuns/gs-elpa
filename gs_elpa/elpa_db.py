#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    elpa_db.py
    ~~~~~~~~~~

    ELPA package database

    :copyright: (c) 2013-2023 Jauhien Piatlicki and others
    :license: GPL-2, see LICENSE for more details.
"""

import sexpdata

from g_sorcery.compatibility import basestring, py2k

if py2k:
    from urlparse import urljoin
else:
    from urllib.parse import urljoin

from g_sorcery.g_collections import Dependency, Package, serializable_elist
from g_sorcery.package_db import DBGenerator
from g_sorcery.exceptions import SyncError


class ElpaDBGenerator(DBGenerator):
    """
    Implementation of database generator for ELPA backend.
    """
    def get_download_uries(self, common_config, config):
        """
        Download database file from REPO_URI/archive-contents
        and parse it with sexpdata.

        Args:
            common_config: Backend config.
            config: Repository config.

        Returns:
            List with one URI entry.
        """
        ac_uri = urljoin(config["repo_uri"], 'archive-contents')
        return [{"uri": ac_uri, "parser": sexpdata.load}]

    def process_data(self, pkg_db, data, common_config, config):
        """
        Process downloaded and parsed data and generate tree.

        Args:
            pkg_db: Package database.
            data: Dictionary with data, keys are file names.
            common_config; Backend config.
            config: Repository config.
        """
        archive_contents = data['archive-contents']
        repo_uri = config["repo_uri"]

        if sexpdata.car(archive_contents) != 1:
            raise SyncError(
                'sync failed: ' + repo_uri + ' bad archive contents format')

        category = 'app-emacs'
        pkg_db.add_category(category)
        common_data = {'eclasses': ['g-sorcery', 'gs-elpa'],
                       'maintainer': [{'email': 'gentoo@houseofsuns.org',
                                       'name': 'Markus Walter'}],
                       'homepage': repo_uri,
                       'repo_uri': repo_uri
                       }
        pkg_db.set_common_data(category, common_data)

        PKG_INFO = 2
        PKG_NAME = 0

        INFO_VERSION = 0
        INFO_DEPENDENCIES = 1
        INFO_DESCRIPTION = 2
        INFO_SRC_TYPE = 3

        DEP_NAME = 0
        # DEP_VERSION = 1 #we do not use it at the moment

        for entry in sexpdata.cdr(archive_contents):
            desc = entry[PKG_INFO].I
            realname = str(entry[PKG_NAME])

            if self.in_config([common_config, config], "exclude", realname):
                continue

            # Version numbers with negative elements have been seen
            # in melpa-stable. Skip these packages for now.
            if not all(i >= 0 for i in desc[INFO_VERSION]):
                continue

            pkg = Package("app-emacs", realname,
                          '.'.join(map(str, desc[INFO_VERSION])))
            source_type = str(desc[INFO_SRC_TYPE])

            allowed_ords = (
                set(range(ord('a'), ord('z')))
                | set(range(ord('A'), ord('Z')))
                | set(range(ord('0'), ord('9')))
                | set(list(map(ord, ['+', '_', '-', ' ', '.', '(', ')',
                                     '[', ']', '{', '}', ',']))))
            description = "".join([x for x in desc[INFO_DESCRIPTION]
                                   if ord(x) in allowed_ords])

            deps = desc[INFO_DEPENDENCIES]

            # fix for crappy arhive-contents that have "No commentary."
            # in place of dependency
            if isinstance(deps, basestring):
                deps = []

            dependencies = serializable_elist(separator="\n\t")
            for dep in deps:
                dep = self.convert_dependency(
                    [common_config, config], str(dep[DEP_NAME]),
                    external=False)
                if dep:
                    dependencies.append(dep)

            properties = {'source_type': source_type,
                          'description': description,
                          'dependencies': dependencies,
                          'depend': dependencies,
                          'rdepend': dependencies,
                          'realname': realname,
                          'longdescription': description
                          }
            pkg_db.add_package(pkg, properties)

    def convert_internal_dependency(self, configs, dependency):
        """
        At the moment we have only internal dependencies, each of them
        is just a package name.

        Args:
            configs: Backend and repo configs.
            dependency: Package name.

        Returns:
            Dependency instance with category="app-emacs",
            package="dependency".
        """
        return Dependency("app-emacs", dependency)
