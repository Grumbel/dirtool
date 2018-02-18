# dirtool.py - diff tool for directories
# Copyright (C) 2017 Ingo Ruhnke <grumbel@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from pkg_resources import resource_filename
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeySequence, QIcon, QCursor, QMovie
from PyQt5.QtWidgets import (
    QMenu,
    QHBoxLayout,
    QPushButton,
    QToolButton,
    QFormLayout,
    QStyle,
    QWidget,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QShortcut,
    QVBoxLayout,
    QToolBar
)

from dirtools.fileview.detail_view import DetailView
from dirtools.fileview.thumb_view import ThumbView
from dirtools.fileview.location_line_edit import LocationLineEdit
from dirtools.fileview.filter_line_edit import FilterLineEdit


class ToolButton(QToolButton):
    """QToolButton with the additional ability to attach a secondary
    action to the middle mouse button."""

    sig_middle_click = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._middle_pressed = False

    def mousePressEvent(self, ev):
        if ev.button() != Qt.MiddleButton:
            if self._middle_pressed:
                ev.ignore()
            else:
                super().mousePressEvent(ev)
        else:
            self.setDown(True)
            self._middle_pressed = True

    def mouseReleaseEvent(self, ev):
        if ev.button() != Qt.MiddleButton:
            if self._middle_pressed:
                ev.ignore()
            else:
                super().mouseReleaseEvent(ev)
        else:
            if self._middle_pressed and self.rect().contains(ev.pos()):
                self.sig_middle_click.emit()

            self.setDown(False)
            self._middle_pressed = False

    def mouseMoveEvent(self, ev):
        if self._middle_pressed:
            if not self.rect().contains(ev.pos()):
                self.setDown(False)
            else:
                self.setDown(True)


class FileViewWindow(QMainWindow):

    def __init__(self, controller):
        super().__init__()

        self.controller = controller
        self.actions = self.controller.actions

        self.make_window()
        self.make_menubar()
        self.make_toolbar()
        self.addToolBarBreak()
        self.make_location_toolbar()
        self.make_filter_toolbar()
        self.make_shortcut()

        self.thumb_view.setFocus()

        self.resize(1024, 768)
        self.move(QCursor.pos().x() - self.width() / 2,
                  QCursor.pos().y() - self.height() / 2)

    def closeEvent(self, ev):
        self.controller.on_exit()

    def make_shortcut(self):
        shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_L), self)
        shortcut.setContext(Qt.WindowShortcut)
        shortcut.activated.connect(lambda: self.file_path.setFocus(Qt.ShortcutFocusReason))

        def show_filter():
            self.file_filter.setFocus(Qt.ShortcutFocusReason)
            self.filter_toolbar.show()

        shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_K), self)
        shortcut.setContext(Qt.WindowShortcut)
        shortcut.activated.connect(show_filter)

        shortcut = QShortcut(QKeySequence(Qt.ALT + Qt.Key_Up), self)
        shortcut.setContext(Qt.WindowShortcut)
        shortcut.activated.connect(self.controller.parent_directory)

        shortcut = QShortcut(Qt.Key_Home, self)
        shortcut.setContext(Qt.WindowShortcut)
        shortcut.activated.connect(lambda: self.thumb_view.ensureVisible(0, 0, 1, 1))

        shortcut = QShortcut(Qt.Key_End, self)
        shortcut.setContext(Qt.WindowShortcut)
        shortcut.activated.connect(
            lambda: self.thumb_view.ensureVisible(
                0, self.thumb_view.layout.get_bounding_rect().height(), 1, 1))

        shortcut = QShortcut(Qt.Key_PageUp, self)
        shortcut.setContext(Qt.WindowShortcut)
        shortcut.activated.connect(lambda: self.thumb_view.scroll_by(0, -self.thumb_view.viewport().height()))

        shortcut = QShortcut(Qt.Key_PageDown, self)
        shortcut.setContext(Qt.WindowShortcut)
        shortcut.activated.connect(lambda: self.thumb_view.scroll_by(0, self.thumb_view.viewport().height()))

    def make_window(self):
        self.setWindowTitle("dt-fileview")
        self.setWindowIcon(QIcon(resource_filename("dirtools", "fileview/dt-fileview.svg")))
        self.vbox = QVBoxLayout()
        self.vbox.setContentsMargins(0, 0, 0, 0)

        self.file_view = DetailView(self.controller)
        self.file_view.hide()
        self.thumb_view = ThumbView(self.controller)
        self.file_path = LocationLineEdit(self.controller)
        self.file_filter = FilterLineEdit(self.controller)
        # self.file_filter.setText("File Pattern Here")
        self.file_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.thumb_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.status_bar = self.statusBar()

        self.info = QLabel("lots of files selected")
        self.status_bar.addPermanentWidget(self.info)

        self.vbox.addWidget(self.file_view, Qt.AlignLeft)
        self.vbox.addWidget(self.thumb_view, Qt.AlignLeft)

        vbox_widget = QWidget()
        vbox_widget.setLayout(self.vbox)
        self.setCentralWidget(vbox_widget)

    def hide_filter(self):
        self.filter_toolbar.hide()

    def make_filter_toolbar(self):
        hbox = QHBoxLayout()

        form = QFormLayout()
        label = QLabel("Filter:")
        label.setBuddy(self.file_filter)
        form.addRow(label, self.file_filter)
        form.setContentsMargins(0, 0, 0, 0)
        hbox.addLayout(form)

        help_button = QPushButton("Help")
        help_button.clicked.connect(self.controller.show_filter_help)
        hbox.addWidget(help_button)
        hbox.setContentsMargins(0, 0, 0, 0)

        widget = QWidget()
        widget.setLayout(hbox)

        self.filter_toolbar = QToolBar()
        self.filter_toolbar.addWidget(widget)
        self.addToolBar(Qt.BottomToolBarArea, self.filter_toolbar)
        self.filter_toolbar.hide()

    def make_location_toolbar(self):
        self.location_toolbar = self.addToolBar("Location")
        widget = QWidget()
        form = QFormLayout()
        label = QLabel("Location:")
        label.setBuddy(self.file_path)
        form.addRow(label, self.file_path)
        form.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(form)
        self.location_toolbar.addWidget(widget)

    def make_group_menu(self):
        menu = QMenu("Group Options")
        menu.addAction(self.actions.group_by_none)
        menu.addAction(self.actions.group_by_day)
        menu.addAction(self.actions.group_by_directory)
        return menu

    def make_sort_menu(self):
        menu = QMenu("Sort Options")
        menu.addSeparator().setText("Sort Options")
        menu.addAction(self.actions.sort_directories_first)
        menu.addAction(self.actions.sort_reversed)
        menu.addSeparator().setText("Sort by")
        menu.addAction(self.actions.sort_by_name)
        menu.addAction(self.actions.sort_by_size)
        menu.addAction(self.actions.sort_by_ext)
        menu.addAction(self.actions.sort_by_date)
        menu.addAction(self.actions.sort_by_duration)
        menu.addAction(self.actions.sort_by_aspect_ratio)
        menu.addAction(self.actions.sort_by_framerate)
        menu.addAction(self.actions.sort_by_area)
        menu.addAction(self.actions.sort_by_user)
        menu.addAction(self.actions.sort_by_group)
        menu.addAction(self.actions.sort_by_permission)
        menu.addAction(self.actions.sort_by_random)
        return menu

    def make_view_menu(self):
        menu = QMenu("View Options")
        menu.addSeparator().setText("View Options")
        menu.addAction(self.actions.show_abspath)
        menu.addAction(self.actions.show_basename)
        menu.addSeparator()
        menu.addAction(self.actions.toggle_timegaps)
        return menu

    def make_menubar(self):
        self.menubar = self.menuBar()
        file_menu = self.menubar.addMenu('&File')
        file_menu.addAction(self.actions.parent_directory)
        file_menu.addAction(self.actions.debug)
        file_menu.addAction(self.actions.save_as)
        file_menu.addSeparator()
        file_menu.addAction(self.actions.exit)

        edit_menu = self.menubar.addMenu('&Edit')
        edit_menu.addAction(self.actions.undo)
        edit_menu.addAction(self.actions.redo)
        edit_menu.addSeparator()
        edit_menu.addAction(self.actions.edit_select_all)

        view_menu = self.menubar.addMenu('&View')
        view_menu.addSeparator().setText("View Style")
        view_menu.addAction(self.actions.view_detail_view)
        view_menu.addAction(self.actions.view_icon_view)
        view_menu.addAction(self.actions.view_small_icon_view)
        view_menu.addSeparator().setText("Filter")
        view_menu.addAction(self.actions.show_hidden)
        view_menu.addAction(self.actions.show_filtered)
        view_menu.addSeparator().setText("Path Options")
        view_menu.addAction(self.actions.show_abspath)
        view_menu.addAction(self.actions.show_basename)
        view_menu.addSeparator().setText("Sort Options")
        view_menu.addAction(self.actions.sort_directories_first)
        view_menu.addAction(self.actions.sort_reversed)
        view_menu.addAction(self.actions.sort_by_name)
        view_menu.addAction(self.actions.sort_by_size)
        view_menu.addAction(self.actions.sort_by_ext)
        view_menu.addAction(self.actions.sort_by_duration)
        view_menu.addAction(self.actions.sort_by_aspect_ratio)
        view_menu.addAction(self.actions.sort_by_framerate)
        view_menu.addAction(self.actions.sort_by_area)
        view_menu.addAction(self.actions.sort_by_user)
        view_menu.addAction(self.actions.sort_by_group)
        view_menu.addAction(self.actions.sort_by_permission)
        view_menu.addAction(self.actions.sort_by_random)
        view_menu.addSeparator().setText("Zoom")
        view_menu.addAction(self.actions.zoom_in)
        view_menu.addAction(self.actions.zoom_out)
        view_menu.addSeparator()

        history_menu = self.menubar.addMenu('&History')
        history_menu.addAction(self.actions.back)
        history_menu.addAction(self.actions.forward)

        help_menu = self.menubar.addMenu('&Help')
        help_menu.addAction(self.actions.about)

    def make_toolbar(self):
        self.toolbar = self.addToolBar("FileView")

        button = ToolButton()
        button.setDefaultAction(self.actions.parent_directory)
        button.sig_middle_click.connect(lambda: self.controller.parent_directory(new_window=True))
        button.setIcon(self.actions.parent_directory.icon())
        self.toolbar.addWidget(button)

        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actions.home)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actions.back)
        self.toolbar.addAction(self.actions.forward)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actions.reload)
        self.toolbar.addAction(self.actions.reload_thumbnails)
        self.toolbar.addAction(self.actions.prepare)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actions.undo)
        self.toolbar.addAction(self.actions.redo)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actions.show_hidden)

        button = QToolButton()
        button.setIcon(QIcon.fromTheme("view-restore"))
        button.setMenu(self.make_view_menu())
        button.setPopupMode(QToolButton.InstantPopup)
        self.toolbar.addWidget(button)

        button = QToolButton()
        button.setIcon(QIcon.fromTheme("view-sort-ascending"))
        button.setMenu(self.make_sort_menu())
        button.setPopupMode(QToolButton.InstantPopup)
        self.toolbar.addWidget(button)

        button = QToolButton()
        button.setIcon(QIcon.fromTheme("view-sort-ascending"))
        button.setMenu(self.make_group_menu())
        button.setPopupMode(QToolButton.InstantPopup)
        self.toolbar.addWidget(button)

        self.toolbar.addSeparator()
        # self.toolbar.addAction(self.style().standardIcon(QStyle.SP_FileDialogContentsView),
        #                       "List View", self.show_list_view)
        self.toolbar.addAction(self.style().standardIcon(QStyle.SP_FileDialogContentsView),
                               "Thumbnail View",
                               self.show_thumb_view)
        self.toolbar.addAction(self.style().standardIcon(QStyle.SP_FileDialogDetailedView),
                               "Detail View",
                               self.show_detail_view)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actions.zoom_in)
        self.toolbar.addAction(self.actions.zoom_out)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actions.lod_in)
        self.toolbar.addAction(self.actions.lod_out)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actions.crop_thumbnails)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actions.debug)

        # Spacer to force right alignment for all following widget
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar.addWidget(spacer)

        # Loading icon
        self.loading_movie = QMovie(resource_filename("dirtools", "fileview/icons/gears.gif"))
        self.loading_label = QLabel()
        self.toolbar.addWidget(self.loading_label)

    def show_loading(self):
        self.show_info("Loading...")
        self.loading_label.setMovie(self.loading_movie)
        self.loading_movie.start()
        self.loading_label.show()

    def hide_loading(self):
        self.show_info("")
        self.loading_movie.stop()
        self.loading_label.setMovie(None)
        self.loading_label.setVisible(False)

    def zoom_in(self):
        self.thumb_view.zoom_in()

    def zoom_out(self):
        self.thumb_view.zoom_out()

    def show_detail_view(self):
        self.thumb_view.hide()
        self.file_view.show()

    def show_thumb_view(self):
        self.thumb_view.show()
        self.file_view.hide()

    def set_location(self, path):
        self.file_path.set_location(path)
        self.setWindowTitle("dt-fileview - {}".format(path))

    def set_file_list(self):
        self.file_path.set_unused_text()

    def show_info(self, text):
        self.info.setText("  " + text)

    def show_current_filename(self, filename):
        self.status_bar.showMessage(filename)


# EOF #
