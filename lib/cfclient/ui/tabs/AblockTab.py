#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     ||          ____  _ __
#  +------+      / __ )(_) /_______________ _____  ___
#  | 0xBC |     / __  / / __/ ___/ ___/ __ `/_  / / _ \
#  +------+    / /_/ / / /_/ /__/ /  / /_/ / / /_/  __/
#   ||  ||    /_____/_/\__/\___/_/   \__,_/ /___/\___/
#
#  Copyright (C) 2011-2013 Bitcraze AB
#
#  Crazyflie Nano Quadcopter Client
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""
The ablock tab is used as a console for AssistNow GPS.
"""

__author__ = 'Bitcraze AB'
__all__ = ['AblockTab']

import time
import sys

import logging
logger = logging.getLogger(__name__)

from cflib.crtp.crtpstack import CRTPPacket, CRTPPort

from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import pyqtSlot, pyqtSignal

from cfclient.ui.tab import Tab

ablock_tab_class = uic.loadUiType(sys.path[0] +
                                   "/cfclient/ui/tabs/ablockTab.ui")[0]

class AblockTab(Tab, ablock_tab_class):
    """Ablock tab for showing messages AssistNow from Crazyflie"""
    
    update = pyqtSignal(str)

    def __init__(self, tabWidget, helper, *args):
        super(AblockTab, self).__init__(*args)
        self.setupUi(self)

        self.tabName = "AssistNow"
        self.menuName = "AssistNow"

        self.tabWidget = tabWidget
        self.helper = helper

        self.assist_now_btn.clicked.connect(self.assist_now) 

        self.update.connect(self.printMsg)

        self.helper.cf.ablock.receivedChar.add_callback(self.update.emit)

    def printMsg(self, text):
        self.ablock.insertPlainText(text)

    def assist_now(self):
        """Callback from assistnow button"""
#        print "Hello World"
        if (self.helper.cf.link != None):
            pk = CRTPPacket()
            pk.port = CRTPPort.ABLOCK
            pk.data = "<S>\n"
            self.helper.cf.send_packet(pk)



