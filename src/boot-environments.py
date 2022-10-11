#!/usr/bin/env python3


# Simple ZFS configuration tool written for FreeBSD in PyQt5
# for bectl(1)
# https://www.freebsd.org/cgi/man.cgi?bectl

# Copyright (c) 2020, Simon Peter <probono@puredarwin.org>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import os, sys
import gettext
import re

try:
    from PyQt5 import QtWidgets, QtGui, QtCore
except:
    print("Could not import PyQt5. On FreeBSD, sudo pkg install py39-qt5")

gettext.bindtextdomain('boot-environments', '/usr/local/share/locale')
gettext.textdomain('boot-environments')
_ = gettext.gettext

# https://stackoverflow.com/a/377028
def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


class BootEnvironmentsManager(object):

    def __init__(self):

        self.app = QtWidgets.QApplication(sys.argv)

        self.boot_environments = []
        self.selection_index = -1

        # Window
        self.window = QtWidgets.QMainWindow()
        self.window.setWindowTitle(_('Backup Station'))
        self.window.setMinimumWidth(720)
        self.window.setMinimumHeight(350)
        self.window.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                                        QtWidgets.QSizePolicy.MinimumExpanding))
        self.window.closeEvent = self.quit
        self.layout = QtWidgets.QVBoxLayout()

        # Menu
        self._showMenu()

        # List
        self.be_model = QtGui.QStandardItemModel(0, 5)
        self.list_widget = QtWidgets.QTableView()
        self.list_widget.setModel(self.be_model)
        self.list_widget.horizontalHeader().setStretchLastSection(True)  # Use full width for columns
        self.list_widget.setShowGrid(False)  # Do not show vertical lines
        self.list_widget.verticalHeader().setVisible(False)  # Do not show line numbers
        self.list_widget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)  # Select whole rows
        self.list_widget.setSelectionMode(
        QtWidgets.QAbstractItemView.SingleSelection)  # Only one row at a time can be selected
        self.list_widget.setAlternatingRowColors(True)
        self.layout.addWidget(self.list_widget)
        self.be_model.itemChanged.connect(lambda idx: self.activate(idx))
        self.list_widget.clicked.connect(lambda idx: self.select(idx))

        # Label
        self.label = QtWidgets.QLabel()
        self.label.setText(_("Select the environment the computer should start into or create new"))
        # TODO: Show here which paths may be not covered by the selected Boot Environment. How?
        # TODO: Offer to include EVERYTHING in Boot Environments. How?
        self.label.setWordWrap(True)
        self.layout.addWidget(self.label)

        # Buttons
        self.buttonbox = QtWidgets.QDialogButtonBox()
        reboot_button = self.buttonbox.addButton(QtWidgets.QDialogButtonBox.Ok)
        reboot_button.setText(_("Restart..."))
        reboot_button.setDefault(True)
        reboot_button.clicked.connect(self.reboot)
        new_button = self.buttonbox.addButton(QtWidgets.QDialogButtonBox.Ok)
        new_button.setText(_("New..."))
        new_button.clicked.connect(self.new)
        remove_button = self.buttonbox.addButton(QtWidgets.QDialogButtonBox.Ok)
        remove_button.setText(_("Remove"))
        remove_button.clicked.connect(self.remove)
        self.mount_button = self.buttonbox.addButton(QtWidgets.QDialogButtonBox.Ok)
        self.mount_button.setText(_("Unmount"))
        self.mount_button.setEnabled(False)
        self.mount_button.clicked.connect(self.mount)
        self.layout.addWidget(self.buttonbox)

        # Set window icon with the same name as the main PyQt file plus the png extension
        candidate = os.path.dirname(__file__) + QtCore.QFileInfo(str(__file__)).baseName() + ".png"
        if os.path.exists(candidate):
            print(candidate)
            self.window.setWindowIcon(QtGui.QIcon(candidate))

        widget = QtWidgets.QWidget()
        widget.setLayout(self.layout)
        self.window.setCentralWidget(widget)

        self.window.show()

        self.ext_process = QtCore.QProcess()

        self.refresh_list_with_bectl()
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(False)
        self.timer.timeout.connect(self.refresh_list_with_bectl)
        self.timer.start(3000)

        sys.exit(self.app.exec_())

    def quit(self, event):
        sys.exit(0)

    def refresh_list_with_bectl(self):
        # self.ext_process.finished.connect(self.onProcessFinished)
        self.ext_process.setProgram("bectl")
        self.ext_process.setArguments(["list", "-H"])

        try:
            pid = self.ext_process.start()
            print("bectl list started")
        except:
            print("bectl list cannot be launched.")
            return  # Stop doing anything here

        i = 0
        self.boot_environments = []
        while self.ext_process.waitForFinished(-1):

            QtWidgets.QApplication.processEvents()  # Important trick so that the app stays responsive without the need for threading!

            while self.ext_process.canReadLine():
                if i == 0:
                    self.be_model.clear()  # This removes the column headings as well
                    self.be_model.setHorizontalHeaderLabels(
                        ['', _('Boot Environment'), _('Active'), _('Mountpoint'), _('Space'), _('Created')])

                i = i + 1
                # This is a really crude attempt to read line-wise. TODO: Do more elegant, like in 'Mount Disk Image.app'
                line = str(self.ext_process.readLine())
                parts = line.split("\\t")
                name = parts[0].replace("b'", "")
                self.boot_environments.append(name)
                active = parts[1]
                is_active_on_reboot = False
                if active == "NR":
                    active = _("Now and on reboot")
                    is_active_on_reboot = True
                if active == "N":
                    active = _("Now")
                if active == "R":
                    active = _("On reboot")
                    is_active_on_reboot = True
                mountpoint = parts[2]
                space = parts[3]
                timestamp = parts[4].replace("\\n'", "")
                # print(name)

                # Create checkbox
                checkbox_item = QtGui.QStandardItem(False)
                checkbox_item.setCheckable(True)
                checkbox_item.setTristate(False)
                if is_active_on_reboot:
                    checkbox_item.setCheckState(QtCore.Qt.Checked)
                else:
                    checkbox_item.setCheckState(QtCore.Qt.Unchecked)

                item = [checkbox_item, QtGui.QStandardItem(name), QtGui.QStandardItem(active),
                        QtGui.QStandardItem(mountpoint), QtGui.QStandardItem(space), QtGui.QStandardItem(timestamp)]
                rows_so_far = self.be_model.rowCount()
                self.be_model.appendRow(item)
                self.list_widget.horizontalHeader().setSectionResizeMode(
                    QtWidgets.QHeaderView.ResizeToContents)  # Auto width for columns depending on contents
                # Set active row selected if no other one should be selected
                if self.selection_index == -1:
                    if is_active_on_reboot:
                        # print("is_active_on_reboot")
                        self.list_widget.setCurrentIndex(self.be_model.index(rows_so_far, 0))
                # Otherwise, restore previous selection
                # which self.be_model.clear() may have cleared
                elif self.selection_index == i - 1:
                    self.list_widget.setCurrentIndex(self.be_model.index(rows_so_far, 0))

        print("populate_list_with_bectl done")

    def reboot(self):
        print("Reboot clicked")

        reply = QtWidgets.QMessageBox.question(
            self.window,
            _("Restart"),
            _("Are you sure you want to restart your computer now?\nAll unsaved work will be lost."),
            QtWidgets.QMessageBox.Cancel,
            QtWidgets.QMessageBox.Ok
        )

        if reply == QtWidgets.QMessageBox.Ok:
            p4 = QtCore.QProcess()
            p4.setProgram("sudo")
            p4.setArguments(["shutdown", "-r", "now"])
            p4.startDetached()

    def select(self, idx):

        self.timer.stop()  # Need to stop the timer here, otherwise we can collide with a refresh and crash

        row = idx.row()
        print("Selected: %s" % row)
        self.selection_index = idx.row()

        self.update_mount_button(row)

        self.timer.start()

    def update_mount_button(self, index):
        boot_environment = self.boot_environments[index]
        if len(self.be_model.itemData(self.be_model.index(self.selection_index, 3))) > 0:
            mountpoint = self.be_model.itemData(self.be_model.index(self.selection_index, 3))[0]
            print(mountpoint)
            if mountpoint == "/":
                self.mount_button.setText(_("Unmount"))
                self.mount_button.setEnabled(False)
            else:
                self.mount_button.setEnabled(True)
            if mountpoint == "-":
                # Is not mounted yet, so we want to mount
                self.mount_button.setText(_("Mount"))
            else:
                # Is already mounted, so we want to unmount
                self.mount_button.setText(_("Unmount"))

    def doubleClicked(self, idx):
        row = idx.row()
        print("doubleClicked: %s" % row)
        # self.selection_index = idx.row()

    def activate(self, idx):
        row = idx.row()
        # print("Activated: %s" % row)
        self.app.setOverrideCursor(
            QtGui.QCursor(QtCore.Qt.WaitCursor))
        self.timer.stop()
        boot_environment = self.boot_environments[row]
        print("Activating: %s" % boot_environment)

        p = QtCore.QProcess()
        p.setProgram("sudo")
        p.setArguments(["-A", "-E", "bectl", "activate", boot_environment])

        try:
            pid = p.start()  # p.startDetached()
            print("bectl activate started")
        except:
            error_string = "bectl activate cannot be launched"
            print(error_string)
            QtWidgets.QMessageBox.critical(
                self.window,
                _("Error"),
                error_string,
                QtWidgets.QMessageBox.Cancel
            )
            return  # Stop doing anything here

        p.waitForFinished(-1)

        if p.exitCode() != 0:
            error_string = str(p.readAll().data(), encoding='utf-8').replace("ERROR: ", "")
            # FIXME: Sometimes we don't get the error message. Possibly we need to use
            # something more complicated, like a QEventLoop?
            # https://forum.qt.io/topic/75454/qprocess-readall-and-qprocess-readallstandardoutput-both-return-an-empty-string-after-qprocess-write-is-run
            if error_string == "":
                error_string = _("Could not activate Boot Environment")
            QtWidgets.QMessageBox.critical(
                self.window,
                _("Error"),
                error_string,
                QtWidgets.QMessageBox.Cancel
            )

        self.refresh_list_with_bectl()
        self.app.setOverrideCursor(
            QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.timer.start()

        self.update_mount_button(row)

    def new(self, sender):
        text, ok = QtWidgets.QInputDialog.getText(self.window, _("New"),
                                                  _("Boot Environment Name:"), QtWidgets.QLineEdit.Normal,
                                                  "")
        if ok and text:

            text = text.replace(" ", "-")  # Replace space with '-'
            text = re.sub('[^A-Za-z0-9\-]+', '', text)  # Remove remaining special characters

            print(text)

            self.app.setOverrideCursor(
                QtGui.QCursor(QtCore.Qt.WaitCursor))
            self.timer.stop()

            p2 = QtCore.QProcess()
            p2.setProgram("sudo")
            p2.setArguments(["-A", "-E", "bectl", "create", text])

            try:
                pid = p2.start()  # p.startDetached()
                print(_("bectl create started"))
            except:
                error_string = _("bectl create cannot be launched")
                print(error_string)
                QtWidgets.QMessageBox.critical(
                    self.window,
                    _("Error"),
                    error_string,
                    QtWidgets.QMessageBox.Cancel
                )
                return  # Stop doing anything here

            p2.waitForFinished(-1)

            if p2.exitCode() != 0:
                error_string = str(p2.readAll().data(), encoding='utf-8').replace("ERROR: ", "")
                # FIXME: Sometimes we don't get the error message. Possibly we need to use
                # something more complicated, like a QEventLoop?
                # https://forum.qt.io/topic/75454/qprocess-readall-and-qprocess-readallstandardoutput-both-return-an-empty-string-after-qprocess-write-is-run
                if error_string == "":
                    error_string = _("Could not create Boot Environment")
                QtWidgets.QMessageBox.critical(
                    self.window,
                    _("Error"),
                    error_string,
                    QtWidgets.QMessageBox.Cancel
                )

            self.refresh_list_with_bectl()
            self.app.setOverrideCursor(
                QtGui.QCursor(QtCore.Qt.ArrowCursor))

            self.timer.start()

    def remove(self):
        # print("Remove: %s" % self.selection_index)

        if self.selection_index < 0:
            return

        boot_environment = self.boot_environments[self.selection_index]

        reply = QtWidgets.QMessageBox.question(
            self.window,
            _("Remove"),
            _("Do you really want to remove %s?\nThis cannot be undone.") % boot_environment,
            QtWidgets.QMessageBox.Cancel,
            QtWidgets.QMessageBox.Ok
        )

        if reply == QtWidgets.QMessageBox.Ok:
            print(_("Removing: %s") % boot_environment)
            self.app.setOverrideCursor(
                QtGui.QCursor(QtCore.Qt.WaitCursor))
            self.timer.stop()

            p3 = QtCore.QProcess()
            p3.setProgram("sudo")
            p3.setArguments(["-A", "-E", "bectl", "destroy", "-Fo", boot_environment])

            try:
                pid = p3.start()  # p.startDetached()
                print(_("bectl destroy started"))
            except:
                error_string = _("bectl destroy cannot be launched")
                print(error_string)
                QtWidgets.QMessageBox.critical(
                    self.window,
                    _("Error"),
                    error_string,
                    QtWidgets.QMessageBox.Cancel
                )
                return  # Stop doing anything here

            p3.waitForFinished(-1)

            if p3.exitCode() != 0:
                error_string = str(p3.readAll().data(), encoding='utf-8').replace("ERROR: ", "")
                # FIXME: Sometimes we don't get the error message. Possibly we need to use
                # something more complicated, like a QEventLoop?
                # https://forum.qt.io/topic/75454/qprocess-readall-and-qprocess-readallstandardoutput-both-return-an-empty-string-after-qprocess-write-is-run
                if error_string == "":
                    error_string = _("Could not destroy Boot Environment")
                QtWidgets.QMessageBox.critical(
                    self.window,
                    _("Error"),
                    error_string,
                    QtWidgets.QMessageBox.Cancel
                )

            self.refresh_list_with_bectl()
            self.app.setOverrideCursor(
                QtGui.QCursor(QtCore.Qt.ArrowCursor))

            self.timer.start()

    def mount(self):
        # print("Mount: %s" % self.selection_index)

        if self.selection_index < 0:
            return

        boot_environment = self.boot_environments[self.selection_index]
        mountpoint = self.be_model.itemData(self.be_model.index(self.selection_index, 3))[0]
        print(mountpoint)

        self.update_mount_button(self.selection_index)

        if mountpoint == "-":
            # Is not mounted yet, so we want to mount
            command = "mount"
        else:
            # Is already mounted, so we want to unmount
            command = "unmount"

        self.app.setOverrideCursor(
            QtGui.QCursor(QtCore.Qt.WaitCursor))
        self.timer.stop()

        p4 = QtCore.QProcess()
        p4.setProgram("sudo")
        p4.setArguments(["-A", "-E", "bectl", command, boot_environment])
        print(p4.program() + " " + " " .join(p4.arguments()))

        try:
            pid = p4.start()  # p.startDetached()
            print("bectl %s started" % command)
        except:
            error_string = _("bectl %s cannot be launched") % command
            print(error_string)
            QtWidgets.QMessageBox.critical(
                self.window,
                _("Error"),
                error_string,
                QtWidgets.QMessageBox.Cancel
            )
            return  # Stop doing anything here

        p4.waitForFinished(-1)

        if p4.exitCode() != 0:
            error_string = str(p4.readAll().data(), encoding='utf-8').replace("ERROR: ", "")
            # FIXME: Sometimes we don't get the error message. Possibly we need to use
            # something more complicated, like a QEventLoop?
            # https://forum.qt.io/topic/75454/qprocess-readall-and-qprocess-readallstandardoutput-both-return-an-empty-string-after-qprocess-write-is-run
            if error_string == "":
                error_string = _("Could not %s Boot Environment") % command
            QtWidgets.QMessageBox.critical(
                self.window,
                _("Error"),
                error_string,
                QtWidgets.QMessageBox.Cancel
            )

        self.refresh_list_with_bectl()

        # If we have mounted the Boot Environment, then open it in the file manager
        if command == "mount":
            p5 = QtCore.QProcess()
            p5.setProgram("launch")
            mountpoint = self.be_model.itemData(self.be_model.index(self.selection_index, 3))[0]
            p5.setArguments(["caja", mountpoint])
            try:
                pid = p5.startDetached()
            except:
                pass

        self.app.setOverrideCursor(
            QtGui.QCursor(QtCore.Qt.ArrowCursor))

        self.timer.start()

        self.update_mount_button(self.selection_index)

    def _showMenu(self):
        exitAct = QtWidgets.QAction(_('&Quit'), self.window)
        exitAct.setShortcut(_('Ctrl+Q'))
        exitAct.setStatusTip(_('Exit application'))
        exitAct.triggered.connect(QtWidgets.QApplication.quit)
        menubar = self.window.menuBar()
        fileMenu = menubar.addMenu(_('&File'))
        fileMenu.addAction(exitAct)

        aboutAct = QtWidgets.QAction(_('&About'), self.window)
        aboutAct.setStatusTip(_('About this application'))
        aboutAct.triggered.connect(self._showAbout)

        helpAct = QtWidgets.QAction(_('&Usage'), self.window)
        helpAct.setStatusTip(_('How use this application'))
        helpAct.triggered.connect(self._showHelp)
        helpMenu = menubar.addMenu(_('&Help'))
        helpMenu.addAction(helpAct)
        helpMenu.addAction(aboutAct)

    def _showAbout(self):
        print("showDialog")
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle(_("About"))
#        msg.setIconPixmap(QtGui.QPixmap("./boot-environments.png").scaledToWidth(64, QtCore.Qt.SmoothTransformation))
        msg.setIconPixmap(QtGui.QPixmap(os.path.dirname(__file__) + "/boot-environments.png").scaledToWidth(64, QtCore.Qt.SmoothTransformation))
        candidates = ["COPYRIGHT", "COPYING", "LICENSE"]
        for candidate in candidates:
            if os.path.exists(os.path.dirname(__file__) + "/" + candidate):
                with open(os.path.dirname(__file__) + "/" + candidate, 'r') as file:
                    data = file.read()
                msg.setDetailedText(data)
        msg.setText("<h3>Boot Environments</h3>")
        msg.setInformativeText(
            _("A simple preferences application to modify <a href='https://bsd-pl.org/assets/talks/2018-07-30_1_S%C5%82awomir-Wojciech-Wojtczak_ZFS-Boot-Environments.pdf'>ZFS Boot Environments</a> \
            <br><br>Source code: <a href='https://github.com/helloSystem/Utilities'>https://github.com/helloSystem/Utilities</a>"))
        msg.exec()

    def _showHelp(self):
        print("showDialog")
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle(_("Help"))
        msg.setText(_("<h3>Description and usage</h3>"))
        msg.setInformativeText(
            _("<hr><h4>General information</h4 \
            <p>Boot Environments are bootable clones of snapshots of the working system. \
            Before upgrading or making major changes to the system, it is strongly recommended that you create a safe boot environment to recover after a failure occurs. \
            Note that Boot Environments by default may not cover all locations, such as /home. More details about this can be found at: \
            <p><a href='https://www.freebsd.org/cgi/man.cgi?bectl(8)'><b>BECTL(8)</b></a> \
            <p><a href='https://klarasystems.com/articles/basics-of-zfs-snapshot-management/'><b>Basics of ZFS Snapshot Management</b></a> \
            <p><a href='https://klarasystems.com/articles/managing-boot-environments/'><b>Managing boot environments</b></a> \
            <hr><h4>Using interface elements</h4>\
            <ul><li>Select an active environment for the next system boot and check in the its checkbox. At the same time, the its <b>Status</b> field will be <b>On reboot</b>. \
            The <b>Status</b> field can have the following values: \
            <small><table> \
            <thead> \
            <tr> \
                <th>Values</th> \
                <th>Description</th> \
            </tr> \
            </thead> \
            <tbody> \
            <tr> \
                <td>-</td> \
                <td><pre>       Nonactive</pre></td> \
            </tr> \
            <tr> \
                <td>Now</td> \
                <td><pre>       Active now</pre></td> \
            </tr> \
            <tr> \
                <td>On reboot</td> \
                <td><pre>       Will be active on next boot time</pre></td> \
            </tr> \
            <tr> \
                <td>Now and on reboot</td> \
                <td><pre>       Active now and will be active on next boot time</pre></td> \
            </tr> \
            </tbody> \
            </table></small></li>\
            <p><li>Click the button <b>[Restart...]</b> to reboot the system into the selected active environment.</li> \
            <p><li>Highlight a line in the list with the cursor and press the <b>[Mount]</b> button to mount the selected environment.  In this case, its path will be displayed in the <b>Mount point</b> field.</li> \
            <p><li>Highlight a line in the list with the cursor and press the <b>[Umount]</b> button to unmount the selected environment. In this case, the path will not be displayed in the <b>Mount point</b> field.</li> \
            <p><li>Highlight a line in the list with the cursor and press the <b>[Remove]</b> button to remove the selected environment. This environment will disappear from the list after confirming the deletion.</li> \
            <p><li>Click the button <b>[New...]</b> to create a new environment. The new environment will appear in the list after entering its name.</b></li></ul> \
            <p> You must have root privileges to work with this program!"))
        msg.exec()

if __name__ == "__main__":
    BootEnvironmentsManager()
