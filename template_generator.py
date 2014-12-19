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
import logging
import subprocess

from ConfigParser import ConfigParser

from pootle_translationproject.models import TranslationProject
from pootle.scripts.actions import TranslationProjectAction


logger = logging.getLogger(__name__)


def _find_current_template(po_path): 
    for filename in os.listdir(po_path):
        if filename.endswith('.pot'):
            return filename
    return None


class TemplateGenerator:

    MSGCMP = "msgcmp %s %s "\
             "--use-untranslated"

    MSGMERGE = "msgmerge %s %s "\
               "--update "\
               "--previous"

    XGETTEXT = "xgettext %s "\
               "--join-existing "\
               "--language=Python "\
               "--keyword=_ "\
               "--output=%s"

    INTLTOOL = "intltool-update "\
               "--pot "\
               "--gettext-package=new"

    FIND = "echo $(find %s -iname \"*.py\")"

    def __init__(self, ref, podir):
        self._ref = ref
        self._podir = podir
        self._root = os.path.dirname(podir)
        self._def = os.path.join(podir, 'new.pot')
        self._potfiles = os.path.join(self._podir, 'POTFILES.in')
        self._info = os.path.join(self._root, 'activity/activity.info')

    def _changed(self):
        cmd = self.MSGCMP % (self._ref, self._def)
        return subprocess.call(cmd, shell=True) != 0

    def _merge(self):
        cmd = self.MSGMERGE % (self._ref, self._def)
        subprocess.call(cmd, shell=True)

    def _generate_activity(self):
        info = ConfigParser()
        info.read(self._info)

        content = ''
        for option in ['name', 'summary', 'description']:
            if info.has_option('Activity', option):
                content += 'msgid "%s"\n' % info.get('Activity', option)
                content += 'msgstr ""\n\n'

        if content:
            with open(self._def, 'w') as file:
                file.write(content)

    def _generate_intltool(self):
        os.chdir(self._podir)
        subprocess.call(self.INTLTOOL, shell=True)

    def _generate_xgettext(self):
        cmd = self.FIND % self._root
        files = subprocess.check_output(cmd, shell=True)
        cmd = self.XGETTEXT % (files.strip(), self._def)
        subprocess.call(cmd, shell=True)

    def generate(self):
        # Remove previous attemps
        if os.path.exists(self._def):
            os.remove(self._def)

        # Populate new.pot with activity.info
        if os.path.exists(self._info):
            self._generate_activity()

        if os.path.exists(self._potfiles):
            self._generate_intltool()
        else:
            self._generate_xgettext()

    def update(self):
        if not self._changed():
            raise Exception('Template is up-to-date, no changes required.')
        self._merge()


class TemplateUpdater(TranslationProjectAction):
    """
    Update source code, template and translations
    """

    def __init__(self, **kwargs):
        super(TemplateUpdater, self).__init__(**kwargs)
        self.icon = 'icon-update-templates'
        self.permission = 'administrate'

    def run(self, **kwargs):
        logger.warning(str(kwargs))

        # update code before updating the template
        directory = kwargs.get('path')
        translation = TranslationProject.objects.get(directory=directory)
        translation.update_dir(directory=directory)

        tp_dir = kwargs.get('tpdir')
        po_dir = kwargs.get('root')
        vcs_dir = kwargs.get('vc_root')

        po_path = os.path.join(po_dir, tp_dir)
        vcs_path = os.path.join(vcs_dir, tp_dir)
        clone_path = os.path.realpath(vcs_path)
        logger.warning(clone_path)

        pot_name = _find_current_template(po_path)
        if not pot_name:
            self.set_error('Could not find current template')
            return

        pot_path = os.path.join(po_path, pot_name)
        logger.warning(pot_path)

        try:
            generator = TemplateGenerator(pot_path, clone_path)
            generator.generate()
            generator.update()
        except Exception as e:
            self.set_error(str(e))
            return

        # update all translations with the new template
        project = translation.project
        translations = TranslationProject.objects.filter(project=project)
        for translation in translations:
            translation.update_against_templates()

        self.set_error('All project\'s translations have been updated')

category = "Manage"
title = "SUGAR: UPDATE _ALL_ FROM REPO SOURCE CODE"
TemplateUpdater.gen = TemplateUpdater(category=category, title=title)
