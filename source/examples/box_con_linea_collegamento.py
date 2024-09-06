import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPen

class DraggableBox(QGraphicsRectItem):
    def __init__(self, x, y, width, height, items):
        super().__init__(x, y, width, height)
        self.setFlag(QGraphicsRectItem.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable)
        self.items = []
        for i, item_text in enumerate(items):
            item = QGraphicsTextItem(item_text, self)
            item.setPos(x + 10, y + 10 + i * 20)
            item.setFlag(QGraphicsTextItem.ItemIsMovable)
            self.items.append(item)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Box con Relazioni")
        self.setGeometry(100, 100, 800, 600)

        # Creare la scena
        self.scene = QGraphicsScene()
        
        # Creare i box
        self.box1 = DraggableBox(50, 50, 200, 100, ["Item uno", "Item due"])
        self.box2 = DraggableBox(300, 200, 200, 100, ["Item uno", "Item due"])
        
        # Aggiungere i box alla scena
        self.scene.addItem(self.box1)
        self.scene.addItem(self.box2)
        
        # Creare la vista
        self.view = QGraphicsView(self.scene, self)
        self.setCentralWidget(self.view)

        # Variabili per tracciare la linea
        self.line = None
        self.start_box = None

        self.view.setMouseTracking(True)
        self.view.viewport().installEventFilter(self)

    def eventFilter(self, source, event):
        if event.type() == event.GraphicsSceneMousePress:
            if event.button() == Qt.RightButton:
                item = self.scene.itemAt(event.pos(), self.view.transform())
                if isinstance(item, DraggableBox):
                    self.start_box = item
                    self.line = QGraphicsLineItem()
                    self.line.setPen(QPen(Qt.black, 2))
                    self.scene.addItem(self.line)
                    self.line.setLine(item.rect().center().x(), item.rect().center().y(), event.pos().x(), event.pos().y())
        elif event.type() == event.GraphicsSceneMouseMove and self.line:
            self.line.setLine(self.start_box.rect().center().x(), self.start_box.rect().center().y(), event.pos().x(), event.pos().y())
        elif event.type() == event.GraphicsSceneMouseRelease and self.line:
            item = self.scene.itemAt(event.pos(), self.view.transform())
            if isinstance(item, DraggableBox) and item != self.start_box:
                self.line.setLine(self.start_box.rect().center().x(), self.start_box.rect().center().y(), item.rect().center().x(), item.rect().center().y())
            else:
                self.scene.removeItem(self.line)
            self.line = None
            self.start_box = None
        return super().eventFilter(source, event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
