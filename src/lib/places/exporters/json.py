#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2013-2018 Paulo Freitas
# MIT License (see LICENSE file)
'''
JSON file exporter module
'''
from __future__ import absolute_import

# Imports

# Built-in dependencies

import io
import json

# Package dependencies

from places.exporters import Exporter
from places.formats.json import JsonFormat

# Classes


class JsonExporter(Exporter):
    '''
    JSON exporter class.
    '''

    # Exporter format
    _format = JsonFormat

    def export(self, **options):
        '''
        Exports the data into a JSON file-like stream.

        Arguments:
            options (dict): The exporting options

        Returns:
            io.BytesIO: A JSON file-like stream

        Raises:
            ExportError: When data fails to export
        '''
        data = self._data.normalize()
        json_data = json.dumps(data,
                               indent=2,
                               separators=(',', ': '),
                               ensure_ascii=False)

        return io.BytesIO(json_data.encode('utf-8'))
