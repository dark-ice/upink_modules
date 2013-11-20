# -*- coding: utf-8 -*-
from openerp import tools
import os
import subprocess
from wkhtmltopdf import wkhtmltopdf


class Odt2Pdf(object):
    def __init__(self, input_file, output_file, encoding='utf-8'):
        self.input_file = input_file
        self.output_file = output_file
        self.encoding = encoding
        self.work_dir = os.path.dirname(input_file)
        defpath = os.environ.get('PATH', os.defpath).split(os.pathsep)
        webkit_path = tools.which('wkhtmltopdf', path=os.pathsep.join(defpath))

    def convert(self):
        pass

    #wkhtmltopdf(url='example.com', output_file='~/example.pdf')