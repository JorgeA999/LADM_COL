"""
/***************************************************************************
    begin                :    09/09/23
    git sha              :    :%H$
    copyright            :    (C) 2020 by Yesid Polania
    email                :    yesidpol.3@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import functools
import locale
import re
from abc import abstractmethod

from qgis.PyQt.QtCore import QObject, pyqtSignal, QProcess, QEventLoop

from asistente_ladm_col.lib.ili.ili2dbargs import get_ili2db_args
from asistente_ladm_col.lib.ili.ili2dbconfig import Ili2DbCommandConfiguration
from asistente_ladm_col.lib.ili.ili2dbutils import (get_java_path,
                                                    get_ili2db_bin,
                                                    JavaNotFoundError)
from asistente_ladm_col.utils.abstract_class import AbstractQObjectMeta


class IliExecutable(QObject, metaclass=AbstractQObjectMeta):
    SUCCESS = 0
    ERROR = 1000
    ILI2DB_NOT_FOUND = 1001

    stdout = pyqtSignal(str)
    stderr = pyqtSignal(str)
    process_started = pyqtSignal(str)
    process_finished = pyqtSignal(int, int)

    __done_pattern = re.compile(r"Info: \.\.\.([a-z]+ )?done")
    _result = None

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.filename = None
        self.tool = None
        self.configuration = self._create_config()
        _, self.encoding = locale.getlocale()

        # Lets python try to determine the default locale
        if not self.encoding:
            _, self.encoding = locale.getdefaultlocale()

        # This might be unset
        # (https://stackoverflow.com/questions/1629699/locale-getlocale-problems-on-osx)
        if not self.encoding:
            self.encoding = 'UTF8'

    @abstractmethod
    def _create_config(self) -> Ili2DbCommandConfiguration:
        """Creates the configuration that will be used by *run* method.

        :return: ili2db configuration"""
        pass

    def _get_ili2db_version(self):
        return self.configuration.db_ili_version

    def _args(self, hide_password):
        """Gets the list of ili2db arguments from configuration.

        :param bool hide_password: *True* to mask the password, *False* otherwise.
        :return: ili2db arguments list.
        :rtype: list
        """
        self.configuration.tool = self.tool

        return get_ili2db_args(self.configuration, hide_password)

    def _ili2db_jar_arg(self):
        ili2db_bin = get_ili2db_bin(self.tool, self._get_ili2db_version(), self.stdout, self.stderr)
        if not ili2db_bin:
            return self.ILI2DB_NOT_FOUND
        return ["-jar", ili2db_bin]

    def _escaped_arg(self, argument):
        if '"' in argument:
            argument = argument.replace('"', '"""')
        if ' ' in argument:
            argument = '"' + argument + '"'
        return argument

    def command(self, hide_password):
        ili2db_jar_arg = self._ili2db_jar_arg()
        args = self._args(hide_password)
        java_path = self._escaped_arg(get_java_path(self.configuration.base_configuration))
        command_args = ili2db_jar_arg + args

        valid_args = []
        for command_arg in command_args:
            valid_args.append(self._escaped_arg(command_arg))

        command = java_path + ' ' + ' '.join(valid_args)

        return command

    def command_with_password(self, edited_command):
        if '--dbpwd ******' in edited_command:
            args = self._args(False)
            i = args.index('--dbpwd')
            edited_command = edited_command.replace('--dbpwd ******', '--dbpwd '+args[i+1])
        return edited_command

    def command_without_password(self, edited_command=None):
        if not edited_command:
            return self.command(True)
        regex = re.compile('--dbpwd [^ ]*')
        match = regex.match(edited_command)
        if match:
            edited_command = edited_command.replace(match.group(1), '--dbpwd ******')
        return edited_command

    def run(self, edited_command=None):
        proc = QProcess()
        proc.readyReadStandardError.connect(
            functools.partial(self.stderr_ready, proc=proc))
        proc.readyReadStandardOutput.connect(
            functools.partial(self.stdout_ready, proc=proc))

        if not edited_command:
            ili2db_jar_arg = self._ili2db_jar_arg()
            if ili2db_jar_arg == self.ILI2DB_NOT_FOUND:
                return self.ILI2DB_NOT_FOUND
            args = self._args(False)
            java_path = get_java_path(self.configuration.base_configuration)
            proc.start(java_path, ili2db_jar_arg + args)
        else:
            proc.start(self.command_with_password(edited_command))

        if not proc.waitForStarted():
            proc = None

        if not proc:
            raise JavaNotFoundError()

        self.process_started.emit(self.command_without_password(edited_command))

        self._result = self.ERROR

        loop = QEventLoop()
        proc.finished.connect(loop.exit)
        loop.exec()

        self.process_finished.emit(proc.exitCode(), self._result)
        return self._result

    def _search_custom_pattern(self, text):
        pass

    def stderr_ready(self, proc):
        text = bytes(proc.readAllStandardError()).decode(self.encoding)

        if self.__done_pattern.search(text):
            self._result = self.SUCCESS

        self._search_custom_pattern(text)

        self.stderr.emit(text)

    def stdout_ready(self, proc):
        text = bytes(proc.readAllStandardOutput()).decode(self.encoding)
        self.stdout.emit(text)
