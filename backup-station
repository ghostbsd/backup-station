#!/usr/bin/env python

import bectl
import crypt
import gi
import os
import pwd

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

class BackupStationWindow(Gtk.Window):
    def createBEList(self):
        data = bectl.get_be_list()
        data.pop(0)

        for element in data:
            self.liststore.append(element.split())

    def selectBE(self):
        selection = self.treeview.get_selection()
        model, paths = selection.get_selected_rows()

        for path in paths:
            iter = model.get_iter(path)
            bename = model.get_value(iter, 0)

        return bename

    # Window and callback used to create a BE.
    def createBEWindow(self, button):
        window = PopupEntryWindow(self.create_callback)
        window.show_all()

    def create_callback(self, text):
        bectl.create_be(text)
        self.liststore.clear()
        self.createBEList()

    # Window and callback used to rename a BE.
    def rename_callback(self, text):
        bename = self.selectBE()
        bectl.rename_be(bename, text)
        self.liststore.clear()
        self.createBEList()

    def renameBEWindow(self, button):
        window = PopupEntryWindow(self.rename_callback)
        window.show_all()

    def activateBE(self, button):
        bename = self.selectBE()
        bectl.activate_be(bename)
        self.liststore.clear()
        self.createBEList()

    def deleteBE(self, button):
        bename = self.selectBE()
        bectl.destroy_be(bename)
        self.liststore.clear()
        self.createBEList()

    def __init__(self):
        super().__init__(title="Backup Station")

        # Create the liststore of boot environments.
        self.liststore = Gtk.ListStore(str, str, str, str, str, str)
        self.createBEList()
        self.treeview = Gtk.TreeView(model=self.liststore)

        # Create columns for the data
        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn("BE", renderer_text, text=0)
        self.treeview.append_column(column_text)

        column_text = Gtk.TreeViewColumn("Active", renderer_text, text=1)
        self.treeview.append_column(column_text)

        column_text = Gtk.TreeViewColumn("Mountpoint", renderer_text, text=2)
        self.treeview.append_column(column_text)

        column_text = Gtk.TreeViewColumn("Space", renderer_text, text=3)
        self.treeview.append_column(column_text)

        column_text = Gtk.TreeViewColumn("Date", renderer_text, text=4)
        self.treeview.append_column(column_text)

        column_text = Gtk.TreeViewColumn("Time", renderer_text, text=5)
        self.treeview.append_column(column_text)

        # Create the buttons to manipulate the BE's
        createButton = Gtk.Button.new_with_label("Create BE")
        createButton.connect("clicked", self.createBEWindow)

        renameButton = Gtk.Button.new_with_label("Rename BE")
        renameButton.connect("clicked", self.renameBEWindow)

        activateButton = Gtk.Button.new_with_label("Activate BE")
        activateButton.connect("clicked", self.activateBE)

        deleteButton = Gtk.Button.new_with_label("Delete BE")
        deleteButton.connect("clicked", self.deleteBE)

        # Create boxes to hold the treeview columns and the row of buttons
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        hbox.pack_start(createButton, True, True, 0)
        hbox.pack_start(renameButton, True, True, 0)
        hbox.pack_start(deleteButton, True, True, 0)
        hbox.pack_start(activateButton, True, True, 0)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        vbox.pack_start(self.treeview, True, True, 0)
        vbox.pack_start(hbox, True, True, 0)
        self.add(vbox)
        self.connect("destroy", Gtk.main_quit)

class PopupEntryWindow(Gtk.Window):
    def clicked(self, button):
        self.callback(self.entry.get_text())
        self.destroy()

    def __init__(self, callback):
        super().__init__(title="BE Name Entry")
        self.callback = callback
        box = Gtk.Box()
        self.add(box)

        self.entry = Gtk.Entry()
        box.pack_start(self.entry, True, True, 0)

        button = Gtk.Button('OK')
        button.connect("clicked", self.clicked)
        box.pack_start(button, True, True, 0)

class not_root(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)
        self.set_title("Backup Station")
        self.connect("delete-event", Gtk.main_quit)
        self.set_size_request(200, 80)
        box1 = Gtk.VBox(homogeneous=False, spacing=0)
        self.add(box1)
        box1.show()
        label = Gtk.Label(label='You need to be root')
        box1.pack_start(label, True, True, 0)
        hBox = Gtk.HBox(homogeneous=False, spacing=0)
        hBox.show()
        box1.pack_end(hBox, False, False, 5)
        ok_button = Gtk.Button()
        ok_button.set_label("OK")
        apply_img = Gtk.Image()
        apply_img.set_from_icon_name('gtk-ok', 1)
        ok_button.set_image(apply_img)
        ok_button.connect("clicked", Gtk.main_quit)
        hBox.pack_end(ok_button, False, False, 5)
        self.show_all()

class confirmation(Gtk.Window):
    def confirm_passwd(self, widget, user):
        pwd_hash = pwd.getpwnam(user).pw_passwd
        password = self.passwd.get_text()
        if crypt.crypt(password, pwd_hash) == pwd_hash:
            self.hide()
            BackupStationWindow().show_all()
        else:
            self.hide()
            self.wrong_password()

    def wrong_password(self):
        window = Gtk.Window()
        window.set_title("Backup Station")
        window.connect("delete-event", Gtk.main_quit)
        window.set_size_request(200, 80)
        box1 = Gtk.VBox(homogeneous=False, spacing=0)
        window.add(box1)
        box1.show()
        label = Gtk.Label(label= 'Wrong password')
        box1.pack_start(label, True, True, 0)
        hBox = Gtk.HBox(homogeneous=False, spacing=0)
        hBox.show()
        box1.pack_end(hBox, False, False, 5)
        ok_button = Gtk.Button()
        ok_button.set_label("OK")
        apply_img = Gtk.Image()
        apply_img.set_from_icon_name('gtk-ok', 1)
        ok_button.set_image(apply_img)
        ok_button.connect("clicked", Gtk.main_quit)
        hBox.pack_end(ok_button, False, False, 5)
        window.show_all()

    def __init__(self, user):
        Gtk.Window.__init__(self)
        self.set_title("Backup Station")
        self.connect("delete-event", Gtk.main_quit)
        self.set_size_request(200, 80)
        vBox = Gtk.VBox(homogeneous=False, spacing=0)
        self.add(vBox)
        vBox.show()
        label = "Confirm password for"
        label = Gtk.Label(label = label + f" {user}")
        vBox.pack_start(label, True, True, 5)
        self.passwd = Gtk.Entry()
        self.passwd.set_visibility(False)
        self.passwd.connect("activate", self.confirm_passwd, user)
        hBox = Gtk.HBox(homogeneous=False, spacing=0)
        hBox.show()
        vBox.pack_start(hBox, False, False, 5)
        hBox.pack_start(self.passwd, True, True, 20)
        hBox = Gtk.HBox(homogeneous=False, spacing=0)
        hBox.show()
        vBox.pack_end(hBox, False, False, 5)
        ok_button = Gtk.Button()
        ok_button.set_label("OK")
        apply_img = Gtk.Image()
        apply_img.set_from_icon_name('gtk-ok', 1)
        ok_button.set_image(apply_img)
        ok_button.connect("clicked", self.confirm_passwd, user)
        hBox.pack_end(ok_button, False, False, 5)
        self.show_all()

if os.geteuid() == 0:
    user = os.getenv("SUDO_USER")
    if user is None:
        BackupStationWindow()
    else:
        confirmation(user)
else:
    not_root()

Gtk.main()