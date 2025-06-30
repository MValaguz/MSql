import sys
import math
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider
from PyQt6.QtCore import QTimer, Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPen, QFont

class GaugeWidget(QWidget):
    def __init__(self, min_value: float, max_value: float, title: str, unit: str,
                 tick_interval: float = None, label_formatter=None, parent=None):
        super().__init__(parent)
        self.min_value = min_value
        self.max_value = max_value
        self.title = title
        self.unit = unit
        self.current_value = min_value
        self.tick_interval = tick_interval
        self.label_formatter = label_formatter
        self.setMinimumSize(200, 200)  # Dimensioni minime per una visualizzazione corretta

    def setValue(self, value: float):
        self.current_value = value
        self.update()  # Richiede il ridisegno del widget

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        size = min(rect.width(), rect.height())
        margin = 10
        radius = (size - 2 * margin) / 2
        center = rect.center()
        
        # Traslazione del sistema di coordinate al centro del widget
        painter.translate(center)

        # Parametri del quadrante: da 135° a 405° (cioè copre 270°)
        start_angle = 135  # in gradi
        span_angle  = 270  # in gradi

        # Disegno dell'arco di fondo
        pen = QPen(Qt.GlobalColor.black, 2)
        painter.setPen(pen)
        gauge_rect = QRectF(-radius, -radius, 2 * radius, 2 * radius)
        painter.drawArc(gauge_rect, int(start_angle * 16), int(span_angle * 16))

        # Disegno delle tacche e dei numeri: se è stato specificato un tick_interval, lo usiamo
        tick_pen = QPen(Qt.GlobalColor.black, 1)
        painter.setPen(tick_pen)
        font = QFont("Arial", 8)
        painter.setFont(font)

        if self.tick_interval is not None:
            tick_values = []
            # calcolo del primo tick maggiore o uguale a min_value
            tick = math.ceil(self.min_value / self.tick_interval) * self.tick_interval
            while tick <= self.max_value:
                tick_values.append(tick)
                tick += self.tick_interval

            for tick in tick_values:
                ratio = (tick - self.min_value) / (self.max_value - self.min_value)
                angle_deg = start_angle + ratio * span_angle
                angle = math.radians(angle_deg)

                # Calcolo della posizione dei punti per la tacca
                outer = QPointF(radius * math.cos(angle), radius * math.sin(angle))
                tick_length = 10
                inner = QPointF((radius - tick_length) * math.cos(angle),
                                (radius - tick_length) * math.sin(angle))
                painter.drawLine(inner, outer)

                # Scrittura della label: se esiste una funzione di formattazione la utilizzo
                text_radius = radius - tick_length - 15
                text_x = text_radius * math.cos(angle)
                text_y = text_radius * math.sin(angle) + 5  # correzione verticale
                if self.label_formatter:
                    text = self.label_formatter(tick)
                else:
                    text = f"{int(tick)}"
                fm = painter.fontMetrics()
                text_width = fm.horizontalAdvance(text)
                painter.drawText(int(text_x - text_width / 2), int(text_y), text)
        else:
            # Modalità di default: 10 suddivisioni
            steps = 10
            for i in range(steps + 1):
                value = self.min_value + i * (self.max_value - self.min_value) / steps
                angle_deg = start_angle + i * (span_angle) / steps
                angle = math.radians(angle_deg)
                outer = QPointF(radius * math.cos(angle), radius * math.sin(angle))
                tick_length = 10
                inner = QPointF((radius - tick_length) * math.cos(angle),
                                (radius - tick_length) * math.sin(angle))
                painter.drawLine(inner, outer)
                text_radius = radius - tick_length - 15
                text_x = text_radius * math.cos(angle)
                text_y = text_radius * math.sin(angle) + 5
                text = f"{int(value)}"
                fm = painter.fontMetrics()
                text_width = fm.horizontalAdvance(text)
                painter.drawText(int(text_x - text_width / 2), int(text_y), text)

        # Disegno della lancetta (needle)
        needle_pen = QPen(Qt.GlobalColor.red, 2)
        painter.setPen(needle_pen)
        ratio = (self.current_value - self.min_value) / (self.max_value - self.min_value)
        needle_angle_deg = start_angle + ratio * span_angle
        needle_angle = math.radians(needle_angle_deg)
        needle_length = radius - 20
        end_point = QPointF(needle_length * math.cos(needle_angle),
                            needle_length * math.sin(needle_angle))
        painter.drawLine(QPointF(0, 0), end_point)

        # Disegno del centro della lancetta
        center_radius = 5
        painter.setBrush(Qt.GlobalColor.black)
        painter.drawEllipse(QPointF(0, 0), center_radius, center_radius)

        # Ripristino della trasformazione per disegnare il titolo in alto
        painter.resetTransform()
        painter.setFont(QFont("Arial", 10))
        title_text = f"{self.title} ({self.unit})"
        painter.drawText(rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter, title_text)

class CarSimulator(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.initSimulation()

    def initUI(self):
        self.setWindowTitle("Simulatore Tachimetro e Contagiri")
        # Imposto lo sfondo della finestra in bianco
        self.setStyleSheet("background-color: white;")
        
        # Quadrante della velocità: numeri in multipli di 20 (da 0 a 240 km/h)
        self.speedGauge = GaugeWidget(0, 240, "Velocità", "km/h",
                                      tick_interval=20,
                                      label_formatter=lambda val: f"{int(val)}")
        # Quadrante del contagiri: numeri in multipli di 1000, formattati divisi per 100 (ad es. 1000 -> "10")
        self.rpmGauge = GaugeWidget(800, 7000, "Contagiri", "RPM",
                                    tick_interval=1000,
                                    label_formatter=lambda val: f"{int(val/100)}")

        # Slider per simulare l'acceleratore
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(-100)
        self.slider.setMaximum(100)
        self.slider.setValue(0)  # Acceleratore neutro
        self.slider.setTickInterval(10)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_label = QLabel("Acceleratore: 0")
        self.slider.valueChanged.connect(self.sliderChanged)

        gauges_layout = QHBoxLayout()
        gauges_layout.addWidget(self.speedGauge)
        gauges_layout.addWidget(self.rpmGauge)

        main_layout = QVBoxLayout()
        main_layout.addLayout(gauges_layout)
        main_layout.addWidget(self.slider_label)
        main_layout.addWidget(self.slider)
        self.setLayout(main_layout)

    def initSimulation(self):
        # Stato iniziale della simulazione
        self.speed = 0.0   # km/h
        self.rpm = 800.0   # RPM (regime minimo)
        self.max_speed = 240.0
        self.idle_rpm = 800.0
        self.rpm_factor = 25.0  # Fattore per calcolare gli RPM in funzione della velocità

        # Parametri per accelerazione e decelerazione
        self.accel_factor = 10.0  # km/h al secondo in accelerazione massima
        self.brake_factor = 15.0  # km/h al secondo in frenata
        self.friction = 5.0       # decelerazione naturale (attrito)

        self.timer_interval = 100  # in millisecondi
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateSimulation)
        self.timer.start(self.timer_interval)

    def sliderChanged(self, value):
        self.slider_label.setText(f"Acceleratore: {value}")

    def updateSimulation(self):
        dt = self.timer_interval / 1000.0
        throttle = self.slider.value() / 100.0  # Normalizzazione in [-1, 1]

        # Calcolo della variazione di velocità
        if throttle > 0:
            delta_speed = throttle * self.accel_factor * dt
        elif throttle < 0:
            delta_speed = throttle * self.brake_factor * dt
        else:
            delta_speed = -self.friction * dt if self.speed > 0 else 0

        self.speed += delta_speed
        self.speed = max(0, min(self.speed, self.max_speed))

        # Calcolo degli RPM target in funzione della velocità
        target_rpm = self.idle_rpm + self.speed * self.rpm_factor
        smoothing = 0.1
        self.rpm += smoothing * (target_rpm - self.rpm)
        self.rpm = max(self.idle_rpm, min(self.rpm, 7000))

        # Aggiornamento dei quadranti
        self.speedGauge.setValue(self.speed)
        self.rpmGauge.setValue(self.rpm)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    sim = CarSimulator()
    sim.show()
    sys.exit(app.exec())
