#   --------------------------------------------------------------------------
# Copyright (c) <2017> <Lionel Garcia>
# BE-BI-PM, CERN (European Organization for Nuclear Research)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#   --------------------------------------------------------------------------
#
#   Not fully documented


from __future__ import unicode_literals
from PyQt5.QtWidgets import QTabWidget, QTextEdit


class QLogDialog(QTabWidget):
    '''
    QLogDialog is a QWidget delivering text info to the user
    '''

    def __init__(self, parent=None):
        super(QLogDialog, self).__init__(parent)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setContentsMargins(0, 0, 0, 0)
        self.addTab(self.log, 'Log')
        self.message = QTextEdit()
        self.message.setReadOnly(True)
        self.message.setContentsMargins(0, 0, 0, 0)
        self.addTab(self.message, 'Message')
        self.setFixedHeight(100)

    def add(self, text, type):
        '''
        add allows to add a text content to the log dialog tab
        :param text: text to be displayed
        :param type: 'error' (red text), 'warning' (yellow text) or 'info' (blue text)
        :return:
        '''

        if type is 'warning':
            prefix = 'WARNING'
            color = 'rgb(145, 26, 10)'
        elif type is 'info':
            prefix = 'INFO'
            color = 'rgb(40, 88, 145)'
        elif type is 'error':
            prefix = 'ERROR'
            color = 'rgb(240, 10, 10)'
        elif type is 'process':
            prefix = 'PROCESS'
            color = 'rgb(219, 157, 60)'

        self.log.append('<span style="color:' + color + '">' + prefix + ': ' + text + '</span>')
        self.repaint()