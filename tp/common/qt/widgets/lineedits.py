from __future__ import annotations

from typing import Any

from overrides import override
from Qt.QtCore import Qt, Signal
from Qt.QtWidgets import QWidget, QLineEdit, QTextBrowser
from Qt.QtGui import QFocusEvent, QMouseEvent, QDragEnterEvent, QDragMoveEvent, QDropEvent

from tp.common.qt import validators, dpi, contexts


def line_edit(
		text: str = '', read_only: bool = False, placeholder_text: str = '', tooltip: str = '',
		parent: QWidget | None = None) -> BaseLineEdit:
	"""
	Creates a basic line edit widget.

	:param str text: default line edit text.
	:param bool read_only: whether line edit is read only.
	:param str placeholder_text: line edit placeholder text.
	:param str tooltip: line edit tooltip text.
	:param QWidget parent: parent widget.
	:return: newly created combo box.
	:rtype: BaseLineEdit
	"""

	new_line_edit = BaseLineEdit(text=text, parent=parent)
	new_line_edit.setReadOnly(read_only)
	new_line_edit.setPlaceholderText(str(placeholder_text))
	if tooltip:
		new_line_edit.setToolTip(tooltip)

	return new_line_edit


def text_browser(parent=None):
	"""
	Creates a text browser widget.

	:param QWidget parent: parent widget.
	:return: newly created text browser.
	:rtype: QTextBrowser
	"""

	new_text_browser = QTextBrowser(parent=parent)

	return new_text_browser


class BaseLineEdit(QLineEdit):

	textModified = Signal(object)
	textChanged = Signal(object)
	mousePressed = Signal(QMouseEvent)
	mouseMoved = Signal(QMouseEvent)
	mouseReleased = Signal(QMouseEvent)

	def __init__(
			self, text: str = '', enable_menu: bool = False, placeholder: str = '', tooltip: str = '',
			edit_width: int | None = None, fixed_width: int | None = None, menu_vertical_offset: int = 20,
			parent: QWidget | None = None):
		super().__init__(parent)

		self._value: str | None = None
		self._text_changed_before: str | None = None
		self._enter_pressed: bool = False

		if edit_width:
			self.setFixedWidth(dpi.dpi_scale(edit_width))
		if fixed_width:
			self.setFixedWidth(dpi.dpi_scale(fixed_width))
		self.setPlaceholderText(str(placeholder))
		self.setToolTip(tooltip)

		self.set_value(text)

		self.textEdited.connect(self._on_text_edited)
		self.textModified.connect(self._on_text_modified)
		self.editingFinished.connect(self._on_editing_finished)
		super().textChanged.connect(self._on_text_changed)
		self.returnPressed.connect(self._on_return_pressed)

		self._before_finished = self.value()

	@override
	def focusInEvent(self, arg__1: QFocusEvent) -> None:
		self._before_finished = self.value()
		super().focusInEvent(arg__1)

	@override
	def mousePressEvent(self, arg__1: QMouseEvent) -> None:
		self.mousePressed.emit(arg__1)
		super().mousePressEvent(arg__1)

	@override
	def mouseMoveEvent(self, arg__1: QMouseEvent) -> None:
		self.mouseMoved.emit(arg__1)
		super().mouseMoveEvent(arg__1)

	@override
	def mouseReleaseEvent(self, arg__1: QMouseEvent) -> None:
		self.mouseReleased.emit(arg__1)
		super().mouseReleaseEvent(arg__1)

	def value(self) -> Any:
		"""
		Returns line edit internal value.

		:return: line edit value.
		:rtype: Any
		"""

		return self._value

	def set_value(self, value: Any, update_text: bool = True):
		"""
		Updates value of the line edit.

		:param Any value: line edit value.
		:param bool update_text: whether to update UI text or only internal text value.
		"""

		self._value = value

		if update_text:
			with contexts.block_signals(self):
				self.setText(str(value))

	def _before_after_state(self) -> tuple[Any, Any]:
		"""
		Internal function that returns the before and after state of the line edit.

		:return: before and after state.
		:rtype: tuple[Any, Any]
		"""

		return self._before_finished, self.value()

	def _on_text_edited(self, value: str):
		"""
		Internal callback function that is called each time text is edited by the user.
		Updates internal value without updating UI (UI is already updated).

		:param str value: new line edit text.
		"""

		self.set_value(value, update_text=False)

	def _on_text_modified(self, value: str):
		"""
		Internal callback function that is called each time text is modified by the user (on return or switching out of
		the text box).
		Updates internal value without updating UI (UI is already updated).

		:param str value: text modified value.
		"""

		self.set_value(value, update_text=False)

	def _on_editing_finished(self):
		"""
		Internal callback function that is called when text edit if finished.
		"""

		before, after = self._before_after_state()
		if before != after and not self._enter_pressed:
			self._before_finished = after
			self.textModified.emit(after)

		self._enter_pressed = False

	def _on_text_changed(self, text: str):
		"""
		Internal callback function that is called each time text is changed by the user.

		:param str text: new text.
		"""

		if text != self._text_changed_before:
			self.textChanged.emit(text)

		self._text_changed_before = text

		if not self.hasFocus():
			self._before_finished = text

	def _on_return_pressed(self):
		"""
		Internal callback function that is called when return is pressed by the user.
		"""

		before, after = self._before_after_state()
		if before != after:
			self.textModified.emit(after)
			self._enter_pressed = True


class FolderLineEdit(BaseLineEdit):
	"""
	Custom QLineEdit with drag and drop behaviour for files and folders
	"""

	def __init__(self, parent: QWidget | None = None):
		super().__init__(parent=parent)

		self.setDragEnabled(True)

	@override
	def dragEnterEvent(self, arg__1: QDragEnterEvent) -> None:
		data = arg__1.mimeData()
		urls = data.urls()
		if urls and urls[0].scheme() == 'file':
			arg__1.acceptProposedAction()

	@override
	def dragMoveEvent(self, e: QDragMoveEvent) -> None:
		data = e.mimeData()
		urls = data.urls()
		if urls and urls[0].scheme() == 'file':
			e.acceptProposedAction()

	@override
	def dropEvent(self, arg__1: QDropEvent) -> None:
		data = arg__1.mimeData()
		urls = data.urls()
		if urls and urls[0].scheme() == 'file':
			self.setText(urls[0].toLocalFile())


class EditableLineEditOnClick(QLineEdit):
	"""
	Custom QLineEdit that becomes editable on click or double click.
	"""

	def __init__(
			self, text: str, single: bool = False, double: bool = True, pass_through_clicks: bool = True,
			upper: bool = False, parent: QWidget | None = None):
		super().__init__(text, parent=parent)

		self._upper = upper
		self._validator = validators.UpperCaseValidator()

		if upper:
			self.setValidator(self._validator)
			self.setText(text)

		self.setReadOnly(True)
		self._editing_style = self.styleSheet()
		self._default_style = 'QLineEdit {border: 0;}'
		self.setStyleSheet(self._default_style)
		self.setContextMenuPolicy(Qt.NoContextMenu)
		self.setProperty('clearFocus', True)

		if single:
			self.mousePressEveNT = self.edit_event
		else:
			if pass_through_clicks:
				self.mousePressEvent = self.mouse_click_pass_through
		if double:
			self.mouseDoubleClickEvent = self.edit_event
		else:
			if pass_through_clicks:
				self.mouseDoubleClickEvent = self.mouse_click_pass_through

		self.editingFinished.connect(self._on_editing_finished)

	@override
	def setText(self, arg__1: str) -> None:
		if self._upper:
			arg__1 = arg__1.upper()

		super().setText(arg__1)

	@override
	def focusOutEvent(self, arg__1: QFocusEvent) -> None:
		super().focusOutEvent(arg__1)
		self._edit_finished()

	@override
	def mousePressEvent(self, arg__1: QMouseEvent) -> None:
		arg__1.ignore()

	def mouseReleaseEvent(self, arg__1: QMouseEvent) -> None:
		arg__1.ignore()

	def edit_event(self, event: QMouseEvent):
		"""
		Internal function that overrides mouse press/release event behaviour.

		:param QMouseEvent event: Qt mouse event.
		"""

		self.setStyleSheet(self._editing_style)
		self.selectAll()
		self.setReadOnly(False)
		self.setFocus()
		event.accept()

	def mouse_click_pass_through(self, event: QMouseEvent):
		"""
		Internal function that overrides mouse press/release event behaviour to pass through the click.

		:param QMouseEvent event: Qt mouse event.
		"""

		event.ignore()

	def _edit_finished(self):
		"""
		Internal function that exits from the edit mode.
		"""

		self.setReadOnly(True)
		self.setStyleSheet(self._default_style)
		self.deselect()

	def _on_editing_finished(self):
		"""
		Internal callback function that is called when line edit text is changed.
		"""

		self._edit_finished()
