import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.Qsci import *

QDir.addSearchPath('icons', './qtdesigner/icons/')

class CustomMainWindow(QMainWindow):
    def __init__(self):
        super(CustomMainWindow, self).__init__()

        # -------------------------------- #
        #           Window setup           #
        # -------------------------------- #

        # 1. Define the geometry of the main window
        # ------------------------------------------
        self.setGeometry(300, 300, 800, 400)
        self.setWindowTitle("QScintilla Test")

        # 2. Create frame and layout
        # ---------------------------
        self.__frm = QFrame(self)
        self.__frm.setStyleSheet("QWidget { background-color: #ffeaeaea }")
        self.__lyt = QVBoxLayout()
        self.__frm.setLayout(self.__lyt)
        self.setCentralWidget(self.__frm)
        self.__myFont = QFont()
        self.__myFont.setPointSize(14)

        # 3. Place a button
        # ------------------
        self.__btn = QPushButton("Qsci")
        self.__btn.setFixedWidth(50)
        self.__btn.setFixedHeight(50)
        self.__btn.clicked.connect(self.__btn_action)
        self.__btn.setFont(self.__myFont)
        self.__lyt.addWidget(self.__btn)

        # -------------------------------- #
        #     QScintilla editor setup      #
        # -------------------------------- #

        # ! Make instance of QSciScintilla class!
        # ----------------------------------------
        self.__editor = QsciScintilla()
        self.__editor.setText("This\n")         # Line 1
        self.__editor.append("is\n")            # Line 2
        self.__editor.append("a\n")             # Line 3
        self.__editor.append("QScintilla\n")    # Line 4
        self.__editor.append("test\n")          # Line 5
        self.__editor.append("program\n")       # Line 6
        self.__editor.append("to\n")            # Line 7
        self.__editor.append("illustrate\n")    # Line 8
        self.__editor.append("some\n")          # Line 9
        self.__editor.append("basic\n")         # Line 10
        self.__editor.append("functions.")      # Line 11
        self.__editor.setLexer(None)
        self.__editor.setUtf8(True)             # Set encoding to UTF-8
        self.__editor.setFont(self.__myFont)

        # 1. Text wrapping
        # -----------------
        self.__editor.setWrapMode(QsciScintilla.WrapMode.WrapWord)
        self.__editor.setWrapVisualFlags(QsciScintilla.WrapVisualFlag.WrapFlagByText)
        self.__editor.setWrapIndentMode(QsciScintilla.WrapIndentMode.WrapIndentIndented)

        # 2. End-of-line mode
        # --------------------
        self.__editor.setEolMode(QsciScintilla.EolMode.EolWindows)
        self.__editor.setEolVisibility(False)

        # 3. Indentation
        # ---------------
        self.__editor.setIndentationsUseTabs(False)
        self.__editor.setTabWidth(4)
        self.__editor.setIndentationGuides(True)
        self.__editor.setTabIndents(True)
        self.__editor.setAutoIndent(True)

        # 4. Caret
        # ---------
        self.__editor.setCaretForegroundColor(QColor("#ff0000ff"))
        self.__editor.setCaretLineVisible(True)
        self.__editor.setCaretLineBackgroundColor(QColor("#1f0000ff"))
        self.__editor.setCaretWidth(2)

        # 5. Margins
        # -----------
        # Margin 0 = Line nr margin
        self.__editor.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.__editor.setMarginWidth(0, "0000")
        self.__editor.setMarginsForegroundColor(QColor("#ff888888"))

        # Margin 1 = Symbol margin
        self.__editor.setMarginType(1, QsciScintilla.MarginType.SymbolMargin)
        self.__editor.setMarginWidth(1, "00000")
        sym_0 = QImage("icons:green_dot.png").scaled(QSize(16, 16))
        
        self.__editor.markerDefine(sym_0, 0)
        
        self.__editor.setMarginMarkerMask(1, 0b1111)

        # 6. Margin mouse clicks
        # -----------------------
        self.__editor.setMarginSensitivity(1, True)
        self.__editor.marginClicked.connect(self.__margin_left_clicked)
        self.__editor.marginRightClicked.connect(self.__margin_right_clicked)


        # ! Add editor to layout !
        # -------------------------
        self.__lyt.addWidget(self.__editor)
        self.show()



    def __margin_left_clicked(self, margin_nr, line_nr, state):
        print("Margin clicked (left mouse btn)!")
        print(" -> margin_nr: " + str(margin_nr))
        print(" -> line_nr:   " + str(line_nr))
        print("")
        
        # tolgo il segnalibro
        if state == Qt.KeyboardModifier.ControlModifier:            
            print('elimino!')
            self.__editor.markerDeleteHandle(self.v_marker)            
        else:
            # aggiungo il segnalibro
            self.v_marker = self.__editor.markerAdd(line_nr, 0)        

        print(f"{self.__editor.markerLine(self.v_marker)}")

    def __margin_right_clicked(self, margin_nr, line_nr, state):
        print("Margin clicked (right mouse btn)!")
        print(" -> margin_nr: " + str(margin_nr))
        print(" -> line_nr:   " + str(line_nr))
        print("")



    def __btn_action(self):
        print("Hello World!")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    QApplication.setStyle(QStyleFactory.create('Fusion'))
    myGUI = CustomMainWindow()

    sys.exit(app.exec())