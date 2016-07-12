#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Brazilian territorial distribution data

The MIT License (MIT)

Copyright (c) 2013-2016 Paulo Freitas

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''
# -- Metadata -----------------------------------------------------------------

__author__ = 'Paulo Freitas <me@paulofreitas.me>'
__copyright__ = 'Copyright (c) 2013-2016 Paulo Freitas'
__license__ = 'MIT'
__version__ = '1.0-dev'
__usage__ = '%(prog)s -b BASE -f FORMAT [-m] [-o FILENAME]'
__epilog__ =\
    'Report bugs and feature requests to https://github.com/paulofreitas/dtb-ibge/issues.'

# -- Imports ------------------------------------------------------------------

# Built-in modules

import ftplib
import io
import os
import sys
import urlparse
import zipfile

# Dependency modules

import yaml

# Package modules

import exporters
import parsers

from value_objects import Struct

# -- Classes ------------------------------------------------------------------


class TerritorialData(object):
    _tables = (
        'uf',
        'mesorregiao',
        'microrregiao',
        'municipio',
        'distrito',
        'subdistrito'
    )
    _fields = {
        'uf': (
            'id',
            'nome'
        ),
        'mesorregiao': (
            'id',
            'id_uf',
            'nome'
        ),
        'microrregiao': (
            'id',
            'id_mesorregiao',
            'id_uf',
            'nome'
        ),
        'municipio': (
            'id',
            'id_microrregiao',
            'id_mesorregiao',
            'id_uf',
            'nome'
        ),
        'distrito': (
            'id',
            'id_municipio',
            'id_microrregiao',
            'id_mesorregiao',
            'id_uf',
            'nome'
        ),
        'subdistrito': (
            'id',
            'id_distrito',
            'id_municipio',
            'id_microrregiao',
            'id_mesorregiao',
            'id_uf',
            'nome'
        )
    }

    def __init__(self, base):
        self._base = Struct(base)
        self._name = 'dtb_{}'.format(self._base.year)
        self._cols = []
        self._rows = []
        self._dict = {}
        self._rawdata = None

        for table_name in self._tables:
            self._cols.append('id_' + table_name)
            self._cols.append('nome_' + table_name)
            self._data[table_name] = []

    def load(self, rawdata):
        self._rawdata = rawdata


class TerritorialBase(object):
    def __init__(self, year, logger):
        if not self.bases.get(year):
            raise Exception('This base is not available to download.')

        self._data = TerritorialData(self.bases.get(year))
        self._logger = logger

    @property
    def bases(self):
        return dict(
            (base_data['year'], base_data)
            for base_data in yaml.load(open(
                os.path.join(os.path.dirname(__file__), 'bases.yaml')))
        )

    @property
    def year(self):
        return str(self._data._base.year)

    @property
    def archive(self):
        return self._data._base.archive

    @property
    def file(self):
        return self._data._base.file

    @property
    def format(self):
        return self._data._base.format

    @property
    def sheet(self):
        return self._data._base.sheet

    @property
    def sheet_file(self):
        return os.path.join(os.path.dirname(__file__), '.cache', str(self.year))

    def download(self):
        url_info = urlparse.urlparse(self.archive)
        ftp = ftplib.FTP(url_info.netloc)
        zip_data = io.BytesIO()
        sheet_file = io.BytesIO()

        self._logger.debug('Connecting to FTP server...')
        ftp.connect()

        self._logger.debug('Logging into the FTP server...')
        ftp.login()
        ftp.cwd(os.path.dirname(url_info.path))

        self._logger.info('Retrieving database...')
        ftp.retrbinary(
            'RETR {}'.format(os.path.basename(url_info.path)),
            zip_data.write
        )

        with zipfile.ZipFile(zip_data, 'r') as zip_file:
            self._logger.info('Reading database...')
            sheet_file.write(zip_file.open(self.file).read())

        try:
            os.makedirs(os.path.dirname(self.sheet_file))
        except OSError:
            pass

        open(self.sheet_file, 'wb').write(sheet_file.getvalue())

        return self

    def retrieve(self):
        if not os.path.exists(self.sheet_file):
            self.download()

        sheet_file = io.BytesIO()
        sheet_file.write(open(self.sheet_file, 'rb').read())

        self._data.load(sheet_file.getvalue())

        return self

    def parse(self):
        parser = parsers.FORMATS.get(self.format)

        try:
            self._data = parser(self._data, self._logger).parse()
        except:
            raise Exception('Failed to parse data using the given parser')

        return self

    def export(self, format, minified=False, filename=None):
        if format not in exporters.FORMATS:
            raise Exception('Unsupported output format.')

        exporter = exporters.FORMATS.get(format)

        if minified:
            self._logger.info('Exporting database to minified {} format...' \
                .format(exporter.format))
        else:
            self._logger.info('Exporting database to {} format...' \
                .format(exporter.format))

        data = str(exporter(self._data, minified))
        self._logger.debug('Done.')

        if filename:
            if filename == 'auto':
                filename = 'dtb' + exporter.extension

            with open(filename, 'w') as export_file:
                export_file.write(data)
        else:
            sys.stdout.write(data)
