# dirtool.py - diff tool for directories
# Copyright (C) 2018 Ingo Ruhnke <grumbel@gmail.com>
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


from typing import TYPE_CHECKING

import time

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QTextOption
from PyQt5.QtWidgets import (QWidget, QDialog, QPushButton, QCheckBox,
                             QHBoxLayout, QVBoxLayout, QSizePolicy,
                             QDialogButtonBox, QLabel, QGroupBox,
                             QTextEdit, QFormLayout, QProgressBar)

import bytefmt

from dirtools.mediainfo import split_duration
from dirtools.file_transfer import ConflictResolution
from dirtools.fileview.settings import settings

if TYPE_CHECKING:
    from dirtools.fileview.filesystem_operations import GuiProgress  # noqa: F401


class TransferDialog(QDialog):

    def __init__(self, target_directory: str, parent: QWidget) -> None:
        super().__init__()

        self._target_directory = target_directory
        self._paused = False

        self._make_gui()
        self.resize(600, 400)

        self._timer = self.startTimer(500)
        self._time = time.time()

    def _on_close_checkbox_toggled(self, state):
        settings.set_value("globals/close_on_transfer_completed", state)

    def _on_transfer_canceled(self):
        self._transfer_log_widget.append("transfer canceled")

    def _on_pause_button(self):
        print("transfer pause not implemented")

        if self._paused:
            self._time = time.time() - self._time
            self._paused = False
            self._btn_pause.setText("Pause")
        else:
            self._time = time.time() - self._time
            self._paused = True
            self._btn_pause.setText("Continue")

    def timerEvent(self, ev) -> None:
        if ev.timerId() == self._timer:
            if self._paused:
                msec = int(self._time * 1000)
            else:
                msec = int((time.time() - self._time) * 1000)

            hours, minutes, seconds = split_duration(msec)
            self._time_widget.setText("{:02d}h:{:02d}m:{:02d}s".format(
                hours, minutes, seconds))

    def _make_gui(self) -> None:
        self.setWindowTitle("Transfering files")

        # Widgets
        move_icon = QLabel()
        move_icon.setPixmap(QIcon.fromTheme("stock_folder-move").pixmap(48))
        move_icon.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        header = QLabel("<big>File transfer in progress:</big>")
        header.setTextFormat(Qt.RichText)

        transfer_log_box = QGroupBox("Log:")

        transfer_log_widget = QTextEdit()
        transfer_log_widget.setReadOnly(True)
        transfer_log_widget.setWordWrapMode(QTextOption.NoWrap)
        self._transfer_log_widget = transfer_log_widget

        box = QVBoxLayout()
        box.addWidget(transfer_log_widget)
        transfer_log_box.setLayout(box)

        current_file_box = QGroupBox("Info:")

        current_file_form = QFormLayout()
        dest_label = QLabel("Destination:")
        dest_widget = QLabel(self._target_directory)
        dest_widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._dest_widget = dest_widget

        source_label = QLabel("Source:")
        source_widget = QLabel()
        source_widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._source_widget = source_widget

        progress_label = QLabel("Progress:")
        progress_widget = QProgressBar()
        self._progress_bar = progress_widget

        transfered_label = QLabel("Transfered:")
        transfered_widget = QLabel()
        self._transfered = transfered_widget

        time_label = QLabel("Time passed:")
        time_widget = QLabel()
        self._time_widget = time_widget

        close_checkbox = QCheckBox("Close when finished")
        close_checkbox.setChecked(settings.value("globals/close_on_transfer_completed", True, bool))
        close_checkbox.toggled.connect(self._on_close_checkbox_toggled)
        self._close_checkbox = close_checkbox

        current_file_form.addRow(dest_label, dest_widget)
        current_file_form.addRow(source_label, source_widget)
        current_file_form.addRow(progress_label, progress_widget)
        current_file_form.addRow(transfered_label, transfered_widget)
        current_file_form.addRow(time_label, time_widget)

        current_file_box.setLayout(current_file_form)

        # Widgets.ButtonBox
        button_box = QDialogButtonBox(self)
        button_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        btn_pause = QPushButton(QIcon.fromTheme("media-pause"), "Pause")
        button_box.addButton(btn_pause, QDialogButtonBox.ActionRole)
        self._btn_pause = btn_pause

        btn_cancel = button_box.addButton(QDialogButtonBox.Cancel)
        btn_cancel.setDefault(True)
        self._btn_cancel = btn_cancel

        btn_close = button_box.addButton(QDialogButtonBox.Close)
        self._btn_close = btn_close
        self._btn_close.setVisible(False)

        # Layout
        subvbox = QVBoxLayout()
        subvbox.addWidget(header)
        subvbox.addWidget(transfer_log_box)
        subvbox.addWidget(current_file_box)
        subvbox.addWidget(close_checkbox)

        hbox = QHBoxLayout()
        hbox.addWidget(move_icon)
        hbox.addLayout(subvbox)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(button_box)
        self.setLayout(vbox)

        # Signals
        btn_pause.clicked.connect(self._on_pause_button)
        btn_cancel.clicked.connect(self.reject)
        btn_close.clicked.connect(self.accept)

    def connect(self, progress: 'GuiProgress') -> None:
        progress.sig_move_file.connect(self._on_move_file)
        progress.sig_move_directory.connect(self._on_move_directory)
        progress.sig_copy_file.connect(self._on_copy_file)
        progress.sig_copy_progress.connect(lambda x, y: self._on_copy_progress("", x, y))
        progress.sig_copy_directory.connect(self._on_copy_directory)
        progress.sig_remove_file.connect(self._on_remove_file)
        progress.sig_remove_directory.connect(self._on_remove_directory)
        progress.sig_link_file.connect(self._on_link_file)
        progress.sig_transfer_canceled.connect(self._on_transfer_canceled)
        progress.sig_transfer_completed.connect(self._on_transfer_completed)

    def _on_copy_file(self, src: str, dst: str, resolution: ConflictResolution):
        if resolution == ConflictResolution.SKIP:
            self._transfer_log_widget.append("skipping file {}".format(src))
        else:
            self._transfer_log_widget.append("copying file {} -> {}".format(src, dst))
            self._source_widget.setText(src)
            self._dest_widget.setText(dst)

    def _on_copy_progress(self, src: str, current: int, total: int):
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(current)

        self._transfered.setText("{} / {}".format(bytefmt.humanize(current), bytefmt.humanize(total)))

    def _on_copy_directory(self, src: str, dst: str, resolution: ConflictResolution):
        if resolution == ConflictResolution.SKIP:
            self._transfer_log_widget.append("skipping directory {}".format(src))
        else:
            self._transfer_log_widget.append("copying directory {}".format(src, dst))
            self._source_widget.setText(src)
            self._dest_widget.setText(dst)

    def _on_move_file(self, src: str, dst: str, resolution: ConflictResolution):
        if resolution == ConflictResolution.SKIP:
            self._transfer_log_widget.append("skipping file {}".format(src))
        else:
            self._transfer_log_widget.append("moving file {} -> {}".format(src, dst))
            self._source_widget.setText(src)
            self._dest_widget.setText(dst)

    def _on_move_directory(self, src: str, dst: str, resolution: ConflictResolution):
        if resolution == ConflictResolution.SKIP:
            self._transfer_log_widget.append("skipping directory {}".format(src))
        else:
            self._transfer_log_widget.append("moving directory {} -> {}".format(src, dst))
            self._source_widget.setText(src)
            self._dest_widget.setText(dst)

    def _on_link_file(self, src: str, dst: str, resolution: ConflictResolution):
        if resolution == ConflictResolution.SKIP:
            self._transfer_log_widget.append("skipping directory {}".format(src))
        else:
            self._transfer_log_widget.append("linking {}".format(src, dst))
            self._source_widget.setText(src)
            self._dest_widget.setText(dst)

    def _on_remove_file(self, src: str):
        self._transfer_log_widget.append("removing file {}".format(src))
        self._source_widget.setText(src)

    def _on_remove_directory(self, src: str):
        self._transfer_log_widget.append("removing directory {}".format(src))

    def _on_transfer_completed(self):
        self._transfer_log_widget.append("transfer completed")

        self._btn_cancel.setVisible(False)
        self._btn_close.setVisible(True)

        self.killTimer(self._timer)
        self._timer = None

        if self._close_checkbox.isChecked():
            self.hide()


# EOF #
