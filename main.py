from src import EmbedParams, embed_images_to_large_image
from PyQt5 import QtWidgets, QtGui, QtCore
import cv2
from src import Ui_MainWindow, EmbedParams, embed_image_to_large_image


class DraggableLabel(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super(DraggableLabel, self).__init__(parent)
        self.setMouseTracking(True)
        self.offset = None

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.offset is not None and event.buttons() == QtCore.Qt.LeftButton:
            self.move(self.mapToParent(event.pos() - self.offset))

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.offset = None

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == delete_action:
            self.parent().parent().parent().deleteEmbedImage()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoomIn()
        else:
            self.zoomOut()

    def zoomIn(self):
        self.resize(int(self.width() * 1.1), int(self.height() * 1.1))
        self.parent().parent().parent().n *= 1.1
        self.parent().parent().parent().updateEmbedParams()

    def zoomOut(self):
        self.resize(int(self.width() * 0.9), int(self.height() * 0.9))
        self.parent().parent().parent().n *= 0.9
        self.parent().parent().parent().updateEmbedParams()


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Connect button click events to functions
        self.pushButton_5.clicked.connect(self.openMainImage)
        self.pushButton_6.clicked.connect(self.openEmbedImage)
        self.pushButton_7.clicked.connect(self.embedImage)
        self.pushButton_8.clicked.connect(self.saveImage)

        # Initialize variables
        self.has_embed_image = False
        self.scale_ratio = 1.0
        self.main_image = None
        self.embed_image_label = None
        self.embed_image = None
        self.embed_relative_center_x = 0.5
        self.embed_relative_center_y = 0.5

        self.real_main_image = None
        self.real_embed_image = None
        self.n = 1.0

    def openMainImage(self):
        options = QtWidgets.QFileDialog.Options()
        filePath, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, "Open Image File", "", "Image Files (*.png *.jpg *.bmp *.gif)", options=options)
        if filePath:
            self.readMainImage(filePath)

    def readMainImage(self, filePath):
        main_image = QtGui.QImage(filePath)
        if main_image.isNull():
            QtWidgets.QMessageBox.critical(
                None, "Error", "Invalid image file.")
            return

        real_main_image = cv2.imread(filePath)
        if real_main_image is None:
            QtWidgets.QMessageBox.critical(
                None, "Error", "opencv does not support this path.")
            return

        self.real_main_image = real_main_image
        self.main_image = main_image

        max_width = 1200
        max_height = 800

        self.scale_ratio = min(
            min(max_width / self.main_image.width(), max_height / self.main_image.height()), 1.0)

        main_image = self.main_image.scaled(int(self.main_image.width() * self.scale_ratio), int(
            self.main_image.height() * self.scale_ratio), QtCore.Qt.KeepAspectRatio)

        pixmap = QtGui.QPixmap.fromImage(main_image)
        self.label.setPixmap(pixmap)
        self.label.setFixedSize(pixmap.width(), pixmap.height())
        self.label.setGeometry(0, 0, pixmap.width(), pixmap.height())

        if self.has_embed_image:
            # delete the embedded image
            self.deleteEmbedImage()

    def openEmbedImage(self):
        if self.main_image is None:
            return
        options = QtWidgets.QFileDialog.Options()
        filePath, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, "Open Image File", "", "Image Files (*.png *.jpg *.bmp *.gif)", options=options)
        if filePath:
            embed_image = QtGui.QImage(filePath)
            if embed_image.isNull():
                QtWidgets.QMessageBox.critical(
                    None, "Error", "Invalid image file.")
                return

            real_embed_image = cv2.imread(filePath)
            if real_embed_image is None:
                QtWidgets.QMessageBox.critical(
                    None, "Error", "opencv does not support this path.")
                return

            self.embed_image = embed_image
            self.real_embed_image = real_embed_image

            embed_image = self.embed_image.scaled(int(self.embed_image.width() * self.scale_ratio), int(
                self.embed_image.height() * self.scale_ratio), QtCore.Qt.KeepAspectRatio)

            pixmap = QtGui.QPixmap.fromImage(embed_image)
            if not self.has_embed_image:
                self.embed_image_label = DraggableLabel(self.label)
                self.has_embed_image = True
            self.embed_image_label.setPixmap(pixmap)
            self.embed_image_label.setGeometry(
                0, 0, pixmap.width(), pixmap.height())
            self.embed_image_label.show()

            self.n = 1.0

    def embedImage(self):
        if not self.has_embed_image:
            return
        # Calculate relative position of the embedded image's center relative to the main image's center
        main_image_width = self.label.width()
        main_image_height = self.label.height()
        embed_image_center_x = self.embed_image_label.x() + self.embed_image_label.width() / 2
        embed_image_center_y = self.embed_image_label.y(
        ) + self.embed_image_label.height() / 2

        # Store the relative center position
        self.embed_relative_center_x = embed_image_center_x / main_image_width
        self.embed_relative_center_y = embed_image_center_y / main_image_height

        # print(
        #     f"center: {(self.embed_relative_center_x, self.embed_relative_center_y)}")
        # print(f"scale ratio: {self.scale_ratio}")
        # print(f"n: {self.n}")

        edge_pixels = self.spinBox.value()

        params = EmbedParams(small_edge_cut=0, corrosion=edge_pixels, mask_center_and_scale=([
            self.embed_relative_center_x, self.embed_relative_center_y], self.n),
            use_corner_matching=self.radioButton.isChecked())
        self.real_main_image = embed_image_to_large_image(
            self.real_main_image, self.real_embed_image, params)

        cv2.imwrite(".temp.png", self.real_main_image)
        self.readMainImage(".temp.png")

    def updateEmbedParams(self):
        embed_image = self.embed_image.scaled(
            self.embed_image_label.width(), self.embed_image_label.height(), QtCore.Qt.KeepAspectRatio)
        pixmap = QtGui.QPixmap.fromImage(embed_image)
        self.embed_image_label.setPixmap(pixmap)

    def deleteEmbedImage(self):
        self.n = 1.0
        self.has_embed_image = False
        self.embed_image_label.deleteLater()

    def saveImage(self):
        if self.real_main_image is None:
            return
        options = QtWidgets.QFileDialog.Options()
        filePath, _ = QtWidgets.QFileDialog.getSaveFileName(
            None, "Save Image File", "", "Image Files (*.png *.jpg *.bmp *.gif)", options=options)
        if filePath:
            cv2.imwrite(filePath, self.real_main_image)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
