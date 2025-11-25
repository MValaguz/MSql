#  Creato da.....: Marco Valaguzza
#  Piattaforma...: Python3.13 con libreria pyqt6
#  Data..........: 24/11/2025
#  Descrizione...: Calcolatrice grafica con PyQt6: da notare il metodo appemd_value() che permette
#                  di aggiungere valori al display da programmi esterni (es. MSql_editor.py)

import os
import sys
import ast
import operator
# Librerie grafiche
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
#Amplifico la pathname per ricercare le icone
QDir.addSearchPath('icons', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qtdesigner', 'icons'))

# -------- Parser matematico sicuro --------
class SafeEval:
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.USub: operator.neg,
    }

    @staticmethod
    def eval_expr(expr: str):
        try:
            node = ast.parse(expr, mode='eval').body
            return SafeEval._eval(node)
        except Exception:
            raise ValueError("Invalid expression")

    @staticmethod
    def _eval(node):
        # Numeri (nuovo modo)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value

        # Operazioni binarie
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type in SafeEval.OPERATORS:
                return SafeEval.OPERATORS[op_type](
                    SafeEval._eval(node.left),
                    SafeEval._eval(node.right)
                )

        # Operazioni unarie (es: -5)
        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type in SafeEval.OPERATORS:
                return SafeEval.OPERATORS[op_type](SafeEval._eval(node.operand))

        raise ValueError("Invalid expression")

# -------- Calcolatrice --------
class Calculator(QWidget):
    closed = pyqtSignal()  

    def __init__(self):
        super().__init__()        
        self.build_ui()
    
    def build_ui(self):
        """
            Costruisce l'interfaccia grafica della calcolatrice.
        """
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Display
        self.display = QLineEdit()
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setReadOnly(True)        
        self.display.setStyleSheet("font-size: 32px;")
        main_layout.addWidget(self.display)

        grid = QGridLayout()
        main_layout.addLayout(grid)

        # Aggiornata con % e ±
        buttons = [
                ("C", 0, 0), ("⌫", 0, 1), ("%", 0, 2), ("/", 0, 3),
                ("7", 1, 0), ("8", 1, 1), ("9", 1, 2), ("*", 1, 3),
                ("4", 2, 0), ("5", 2, 1), ("6", 2, 2), ("-", 2, 3),
                ("1", 3, 0), ("2", 3, 1), ("3", 3, 2), ("+", 3, 3),
                ("±", 4, 0), ("0", 4, 1), (",", 4, 2), ("=", 4, 3),
        ]       

        for text, row, col in buttons:
            btn = QPushButton(text)            
            btn.clicked.connect(self.button_clicked)
            grid.addWidget(btn, row, col)
            btn.setStyleSheet("font-size: 30px;")

    def append_value(self, value):
        """
           Aggiunge il valore passato al display della calcolatrice.
           `value` può essere una stringa o un numero.
        """
        if value is None:
            return

        current = self.display.text()
        self.display.setText(current + str(value))
    
    def button_clicked(self):
        """
            Gestione click sui bottoni
        """
        text = self.sender().text()

        if text == "C":
            self.display.setText("")
            return

        if text == "⌫":
            self.display.setText(self.display.text()[:-1])
            return

        if text == "=":
            self.calculate()
            return

        # inversione segno
        if text == "±":
            current = self.display.text()
            if not current:
                return

            # Io → Italiano (virgola)
            current = current.replace(",", ".")
            try:
                val = float(current)
                val = -val
                self.display.setText(str(val).replace(".", ","))
            except:
                self.display.setText("Errore")
            return

        # virgola → punto
        if text == ",":
            self.display.setText(self.display.text() + ".")
            return

        # percentuale: inserisce un simbolo speciale da interpretare
        if text == "%":
            self.display.setText(self.display.text() + "%")
            return

        # aggiungi carattero normale
        self.display.setText(self.display.text() + text)

    def calculate(self):
        """
            Esegue il calcolo dell'espressione nel display.     
        """
        expr = self.display.text()

        # --- Gestione % stile calcolatrice ---
        if "%" in expr:
            expr = self.handle_percent(expr)

        # conversione virgola → punto
        expr = expr.replace(",", ".")

        try:
            result = SafeEval.eval_expr(expr)
            self.display.setText(str(result).replace(".", ","))
        except:
            self.display.setText("Errore")
    
    def handle_percent(self, expr: str) -> str:
        """
            Gestisce le percentuali nello stile delle calcolatrici.
            Esempi:
                "200+10%" → "200+20"
                "150-5%"  → "150-7.5"
                "50%"     → "0.5"
        """
        # Cerca l'ultimo operatore
        for op in ["+", "-", "*", "/"]:
            if op in expr:
                parts = expr.split(op)
                if len(parts) == 2 and "%" in parts[1]:
                    a = parts[0]
                    b = parts[1].replace("%", "")
                    try:
                        a = float(a.replace(",", "."))
                        b = float(b.replace(",", "."))
                        percent_value = a * (b / 100)
                        return f"{a}{op}{percent_value}"
                    except:
                        return "0"
        # Caso semplice: "50%" → 0.5
        return str(float(expr.replace("%", "")) / 100)

    def keyPressEvent(self, event):
        """
            Gestione tasti da tastiera
        """
        key = event.key()
        txt = event.text()

        if key in (
            Qt.Key.Key_0, Qt.Key.Key_1, Qt.Key.Key_2, Qt.Key.Key_3,
            Qt.Key.Key_4, Qt.Key.Key_5, Qt.Key.Key_6, Qt.Key.Key_7,
            Qt.Key.Key_8, Qt.Key.Key_9
        ):
            self.display.setText(self.display.text() + txt)

        elif key in (
            Qt.Key.Key_Plus, Qt.Key.Key_Minus,
            Qt.Key.Key_Slash, Qt.Key.Key_Asterisk
        ):
            self.display.setText(self.display.text() + txt)

        elif key == Qt.Key.Key_Comma:
            self.display.setText(self.display.text() + ".")

        elif key == Qt.Key.Key_Percent:
            self.display.setText(self.display.text() + "%")

        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.calculate()

        elif key == Qt.Key.Key_Backspace:
            self.display.setText(self.display.text()[:-1])

        elif key == Qt.Key.Key_Escape:
            self.display.setText("")
        
    def closeEvent(self, event):
        """
            Evento di chiusura della finestra
        """
        self.closed.emit()   # notifica il chiamante
        super().closeEvent(event)

def run_calculator():
    """
        Avvia la calcolatrice.
        Se esiste già un QApplication (ad esempio richiamata da un altro programma),
        NON ne crea uno nuovo.
    """
    app = QApplication.instance()
    must_exec = False

    if app is None:
        app = QApplication(sys.argv)
        must_exec = True

    win = Calculator()
    win.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
    win.setWindowIcon(QIcon("icons:Calculator.png"))
    win.setWindowTitle("Calculator")
    win.show()
    win.raise_()
    win.activateWindow()

    # Se siamo dentro un altro programma PyQt,
    # NON bloccare il loop degli eventi.
    if must_exec:
        return app.exec()
    else:
        return win

# -------- Main classico --------
if __name__ == "__main__":
    run_calculator()