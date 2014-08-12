#!/usr/bin/env python

# Copyright (c) 2014 Martin Abente Lahaye. - tch@sugarlabs.org
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

import os
import shutil
import fnmatch
import logging
import tempfile
import subprocess

from pootle_project.models import Project
from pootle_misc import versioncontrol as pootle_vcs
from pootle.scripts.actions import TranslationProjectAction

from translate.storage import versioncontrol as store_vcs

logger = logging.getLogger(__name__)


class SourceFinder:

    @staticmethod
    def _find_files(root_path):
        files = []
        for path, dirs, names in os.walk(root_path):
            for filename in fnmatch.filter(names, '*.py'):
                files.append(os.path.join(path, filename))
        return files

    # TODO check po/POTFILES.in
    @staticmethod
    def find(root_path):
        return SourceFinder._find_files(root_path)


class CreationError(Exception):
    pass


class NoChangesError(Exception):
    pass


class POTGenerator:

    POT = "xgettext --language=Python --keyword=_ --keyword=N_ --output=%s %s"
    CMP = 'msgcmp %s %s --use-untranslated'

    @staticmethod
    def generate(path, files):
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_file.close()

        files_str = ' '.join(files)
        cmd = POTGenerator.POT % (tmp_file.name, files_str)
        code = subprocess.call(cmd, shell=True)
        if code != 0:
            raise CreationError('Cannot create template.')

        cmd = POTGenerator.CMP % (path, tmp_file.name)
        code = subprocess.call(cmd, shell=True)
        if code == 0:
            raise NoChangesError('Nothing new for template.')

        shutil.copy(tmp_file.name, path)


class TemplateGenerator(TranslationProjectAction):
    """_
    Generate a template file for a given project
    """

    def __init__(self, **kwargs):
        super(TemplateGenerator, self).__init__(**kwargs)
        self.icon = 'icon-update-templates'
        self.permission = 'administrate'

    def run(self, **kwargs):
        code = kwargs.get('project', None)

        try:
            project = Project.objects.get(code=code)
        except:
            self.set_error('Could not find project code %s' % str(code))
            return

        translation_project = project.get_template_translationproject()
        stores = translation_project.stores.all()

        if not stores:
            return

        store = stores[0]
        path = store.file.name

        pod_path = pootle_vcs.to_podir_path(path)
        vcs_path = pootle_vcs.to_vcs_path(path)
        vcs_object = store_vcs.get_versioned_object(vcs_path)
        vcs_root_dir = vcs_object.root_dir

        files = SourceFinder.find(vcs_root_dir)

        try:
            POTGenerator.generate(pod_path, files)
        except (CreationError, NoChangesError) as e:
            self.set_error(e.message)
            return

        message = 'Commit for updating template'
        author = '%s <%s>' % ('Pootle daemon', 'pootle@pootle.sugarlabs.org')
        pootle_vcs.commit_file(path, message=message, author=author)
        self.set_output('%s has been updated and committed' % path)

category = "Manage"
title = "Generate template"
TemplateGenerator.gen = TemplateGenerator(category=category, title=title)
