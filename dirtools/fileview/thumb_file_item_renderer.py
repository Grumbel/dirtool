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


import logging
from datetime import datetime

from PyQt5.QtCore import Qt, QRect, QMargins
from PyQt5.QtGui import QColor, QPainter, QIcon

import bytefmt

from dirtools.fileview.thumbnail import ThumbnailStatus
from dirtools.mediainfo import split_duration

logger = logging.getLogger(__name__)


def make_scaled_rect(sw, sh, tw, th):
    tratio = tw / th
    sratio = sw / sh

    if tratio > sratio:
        w = sw * th // sh
        h = th
    else:
        w = tw
        h = sh * tw // sw

    return QRect(tw // 2 - w // 2,
                 th // 2 - h // 2,
                 w, h)


def make_unscaled_rect(sw, sh, tw, th):
    return QRect(tw // 2 - sw // 2,
                 th // 2 - sh // 2,
                 sw, sh)


def make_cropped_rect(sw, sh, tw, th):
    """Calculate a srcrect that fits into the dstrect and fills it,
    cropping the src."""

    tratio = tw / th
    sratio = sw / sh

    if tratio > sratio:
        w = sw
        h = th * sw // tw

        return QRect(0,
                     0,  # top align
                     # max(0, sh // 3 - h // 2),
                     # center: sh // 2 - h // 2,
                     w, h)
    else:
        w = tw * sh // tw
        h = sh

        return QRect(sw // 2 - w // 2,
                     0,
                     w, h)


class ThumbFileItemRenderer:

    def __init__(self, item):
        self.fileinfo = item.fileinfo
        self.icon = item.icon
        self.thumbnail = item._get_thumbnail()
        self.level_of_detail = item.thumb_view._level_of_detail
        self.style = item.thumb_view._style
        self.column_style = item.thumb_view._column_style
        self.tile_rect = item.tile_rect
        self.thumbnail_rect = QRect(0, 0, item.tile_rect.width(), item.tile_rect.width())
        self.hovering = item.hovering
        self.animation_timer = item.animation_timer
        self.new = item._new
        self.crop_thumbnails = item.thumb_view._crop_thumbnails
        self.is_selected = item.isSelected()
        self.is_cursor = item.thumb_view._cursor_item == item

    def render(self, painter: QPainter) -> None:
        self.paint(painter)

    def paint(self, painter: QPainter) -> None:
        self.paint_text_items(painter)
        self.paint_thumbnail(painter)

        if self.hovering and self.animation_timer is None:
            painter.setCompositionMode(QPainter.CompositionMode_Overlay)
            painter.setOpacity(0.75)
            self.paint_thumbnail(painter)
            painter.setOpacity(1.0)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        if self.level_of_detail > 1 and not self.column_style:
            self.paint_metadata(painter)
            self.paint_overlay(painter)

        if self.is_selected:
            painter.save()
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setOpacity(0.5)
            painter.fillRect(self.tile_rect, QColor(127, 192, 255))
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setOpacity(1.0)
            painter.setPen(QColor(96, 127, 255))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.tile_rect)
            painter.restore()

        if self.is_cursor:
            painter.setOpacity(1.0)
            painter.setPen(QColor(0, 0, 0))
            painter.setBrush(QColor(255, 255, 255, 96))
            painter.drawRect(self.tile_rect)

    def paint_text_items(self, painter: QPainter) -> None:
        # text items
        if self.level_of_detail > 0:
            self.paint_text_item(painter, 0, self.fileinfo.basename())

        if self.level_of_detail > 2:
            painter.setPen(QColor(96, 96, 96))
            self.paint_text_item(painter, 1, bytefmt.humanize(self.fileinfo.size()))

        if self.level_of_detail > 3:
            dt = datetime.fromtimestamp(self.fileinfo.mtime())
            painter.setPen(QColor(96, 96, 96))
            self.paint_text_item(painter, 2, dt.strftime("%F %T"))

    def paint_text_item(self, painter: QPainter, row: int, text: str) -> None:
        font = self.style.font
        fm = self.style.fm

        tmp = text

        if not self.column_style:
            target_width = self.tile_rect.width()
        else:
            target_width = self.tile_rect.width() - 32 - 4

        if fm.width(tmp) > target_width:
            while fm.width(tmp + "…") > target_width:
                tmp = tmp[0:-1]

        if tmp != text:
            text = tmp + "…"

        painter.setFont(font)

        k = [0, 1, 1, 2, 3][self.level_of_detail]
        if not self.column_style:
            painter.drawText(self.tile_rect.width() / 2 - fm.width(text) / 2,
                             self.tile_rect.height() - 2 + 16 * row - 16 * k + 14,
                             text)
        else:
            painter.drawText(self.tile_rect.height() + 4,
                             self.tile_rect.height() - 2 + 16 * row - 16 * k + 14,
                             text)

    def paint_thumbnail(self, painter: QPainter) -> None:

        if self.column_style:
            self.paint_icon(painter, self.icon)
            return

        thumbnail = self.thumbnail

        if thumbnail.status == ThumbnailStatus.INITIAL:
            self.paint_icon(painter, self.icon)

        elif thumbnail.status == ThumbnailStatus.LOADING:
            self.paint_icon(painter, self.icon)

        elif thumbnail.status == ThumbnailStatus.THUMBNAIL_UNAVAILABLE:
            self.paint_icon(painter, self.icon)

        elif thumbnail.status == ThumbnailStatus.THUMBNAIL_ERROR:
            self.paint_icon(painter, self.icon)

        elif thumbnail.status == ThumbnailStatus.THUMBNAIL_READY:
            pixmap = thumbnail.get_pixmap()
            assert pixmap is not None

            if not self.crop_thumbnails:
                rect = make_scaled_rect(pixmap.width(), pixmap.height(),
                                        self.thumbnail_rect.width(), self.thumbnail_rect.width())
                painter.drawPixmap(rect, pixmap)
            else:
                srcrect = make_cropped_rect(pixmap.width(), pixmap.height(),
                                            self.thumbnail_rect.width(), self.thumbnail_rect.width())
                painter.drawPixmap(self.thumbnail_rect, pixmap, srcrect)

    def paint_metadata(self, painter: QPainter) -> None:
        metadata = self.fileinfo.metadata()

        font = self.style.font
        fm = self.style.fm
        painter.setFont(font)

        top_left_text = ""
        top_right_text = ""
        bottom_left_text = ""

        if self.new:
            painter.drawPixmap(QRect(2, 2, 24, 24),
                               self.style.shared_pixmaps.new)

        if "type" in self.fileinfo.metadata() and self.fileinfo.metadata()["type"] == "error":
            painter.drawPixmap(QRect(2, 2, 24, 24),
                               self.style.shared_pixmaps.error)

        if 'duration' in metadata:
            hours, minutes, seconds = split_duration(metadata['duration'])
            top_left_text = "{:d}:{:02d}:{:02d}".format(hours, minutes, seconds)

        if 'pages' in metadata:
            top_left_text = "{:d} pages".format(metadata['pages'])

        if 'file_count' in metadata:
            top_left_text = "{:d} files".format(metadata['file_count'])

        if 'framerate' in metadata:
            top_right_text = "{:g}fps".format(metadata['framerate'])

        if 'width' in metadata and 'height' in metadata:
            bottom_left_text = "{}x{}".format(metadata['width'], metadata['height'])

        if top_left_text:
            w = fm.width(top_left_text)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 255, 255, 160))
            painter.drawRect(0, 0, w + 4, 16)
            painter.setPen(QColor(0, 0, 0))
            painter.drawText(2, 12, top_left_text)

        if top_right_text:
            w = fm.width(top_right_text)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 255, 255, 160))
            painter.drawRect(self.thumbnail_rect.width() - w - 4, 0, w + 4, 16)
            painter.setPen(QColor(0, 0, 0))
            painter.drawText(self.thumbnail_rect.width() - w - 2, 12, top_right_text)

        if bottom_left_text:
            w = fm.width(bottom_left_text)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 255, 255, 160))
            painter.drawRect(0, self.thumbnail_rect.height() - 16, w + 4, 16)
            painter.setPen(QColor(0, 0, 0))
            painter.drawText(2, self.thumbnail_rect.height() - 4, bottom_left_text)

        if self.fileinfo.is_video():
            painter.setOpacity(0.5)
            # painter.setCompositionMode(QPainter.CompositionMode_Plus)
            painter.drawPixmap(QRect(self.thumbnail_rect.width() - 24 - 2,
                                     self.thumbnail_rect.height() - 24 - 2,
                                     24, 24),
                               self.style.shared_pixmaps.video)
            painter.setOpacity(1.0)
        elif self.fileinfo.is_image():
            painter.setOpacity(0.5)
            # painter.setCompositionMode(QPainter.CompositionMode_Plus)
            painter.drawPixmap(QRect(self.thumbnail_rect.width() - 24 - 2,
                                     self.thumbnail_rect.height() - 24 - 2,
                                     24, 24),
                               self.style.shared_pixmaps.image)
            painter.setOpacity(1.0)

    def paint_overlay(self, painter: QPainter) -> None:
        if self.column_style:
            return

        if self.fileinfo.have_access() is False:
            painter.setOpacity(0.5)
            m = int(self.thumbnail_rect.width() * 0.125)
            painter.drawPixmap(self.thumbnail_rect.marginsRemoved(QMargins(m, m, m, m)),
                               self.style.shared_pixmaps.locked)
            painter.setOpacity(1.0)

        thumbnail = self.thumbnail
        if thumbnail.status == ThumbnailStatus.LOADING or thumbnail.status == ThumbnailStatus.INITIAL:
            painter.setOpacity(0.5)
            painter.drawPixmap(QRect(self.thumbnail_rect.width() - 32,
                                     2,
                                     32, 32),
                               self.style.shared_pixmaps.loading)
            painter.setOpacity(1.0)
        elif thumbnail.status == ThumbnailStatus.THUMBNAIL_ERROR:
            self.paint_icon(painter, self.style.shared_icons.image_error)

    def paint_tiny_icon(self, painter: QPainter, icon: QIcon) -> None:
        painter.setOpacity(0.5)
        icon.paint(painter, QRect(self.tile_rect.width() - 48, 0, 48, 48))

    def paint_icon(self, painter: QPainter, icon: QIcon) -> None:
        if not self.column_style:
            rect = make_unscaled_rect(self.tile_rect.width() * 3 // 4, self.tile_rect.width() * 3 // 4,
                                      self.tile_rect.width(), self.tile_rect.width())
        else:
            rect = QRect(0, 0, self.tile_rect.height(), self.tile_rect.height())

        icon.paint(painter, rect)


# EOF #