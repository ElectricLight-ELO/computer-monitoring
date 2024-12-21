import sys
import psutil
import subprocess
import json
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QLabel, QGridLayout)
from PySide6.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Добавляем импорт для скрытия консоли
import subprocess
from subprocess import CREATE_NO_WINDOW

class SystemMonitorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Мониторинг системы')
        self.setGeometry(100, 100, 1200, 400)

        # Проверяем доступность GPU
        self.gpu_available = self.check_gpu_available()

        # Создаем центральный виджет и layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QGridLayout(central_widget)

        # Создаем графики и контейнеры для информации
        self.cpu_widget = QWidget()
        self.memory_widget = QWidget()
        self.gpu_widget = QWidget()
        
        cpu_layout = QVBoxLayout(self.cpu_widget)
        memory_layout = QVBoxLayout(self.memory_widget)
        gpu_layout = QVBoxLayout(self.gpu_widget)

        # Создаем метки для дополнительной информации
        self.memory_info = QLabel()
        self.gpu_info = QLabel()
        
        # Создаем графики
        self.cpu_canvas = self.create_chart()
        self.memory_canvas = self.create_chart()
        self.gpu_canvas = self.create_chart()

        # Добавляем графики и информацию в layouts
        cpu_layout.addWidget(self.cpu_canvas)
        memory_layout.addWidget(self.memory_canvas)
        memory_layout.addWidget(self.memory_info)
        gpu_layout.addWidget(self.gpu_canvas)
        gpu_layout.addWidget(self.gpu_info)

        # Добавляем виджеты в главный layout
        main_layout.addWidget(self.cpu_widget, 0, 0)
        main_layout.addWidget(self.memory_widget, 0, 1)
        main_layout.addWidget(self.gpu_widget, 0, 2)

        # Таймер для обновления данных
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_charts)
        self.timer.start(2000)  # Обновление каждые 2 секунды

        # Инициализация графиков
        self.cpu_ax = self.cpu_canvas.figure.subplots()
        self.memory_ax = self.memory_canvas.figure.subplots()
        self.gpu_ax = self.gpu_canvas.figure.subplots()
        self.update_charts()

    def create_chart(self):
        fig = Figure(figsize=(4, 4))
        canvas = FigureCanvas(fig)
        return canvas

    def check_gpu_available(self):
        try:
            subprocess.run(['nvidia-smi'], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE, 
                         creationflags=CREATE_NO_WINDOW)
            return True
        except:
            return False

    def get_gpu_info(self):
        try:
            if not self.gpu_available:
                return None
            
            # Получаем информацию о GPU через nvidia-smi в формате CSV
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total,memory.used,utilization.gpu', 
                 '--format=csv,noheader,nounits'],
                stdout=subprocess.PIPE,
                text=True,
                creationflags=CREATE_NO_WINDOW  # Скрываем консоль
            )
            
            # Парсим вывод
            gpu_data = result.stdout.strip().split(',')
            if len(gpu_data) >= 4:
                return {
                    'name': gpu_data[0].strip(),
                    'memory_total': float(gpu_data[1].strip()),
                    'memory_used': float(gpu_data[2].strip()),
                    'load': float(gpu_data[3].strip())
                }
            return None
        except Exception as e:
            print(f"Ошибка при получении информации о GPU: {e}")
            return None

    def update_charts(self):
        # Очищаем графики
        self.cpu_ax.clear()
        self.memory_ax.clear()
        self.gpu_ax.clear()

        # CPU данные
        cpu_usage = psutil.cpu_percent()
        cpu_free = 100 - cpu_usage
        
        # Память данные
        memory = psutil.virtual_memory()
        memory_total = memory.total / (1024**3)
        memory_used = memory.used / (1024**3)
        memory_free = memory.available / (1024**3)

        # GPU данные
        gpu_info = self.get_gpu_info()

        # Обновляем график CPU
        cpu_data = [cpu_usage, cpu_free]
        cpu_labels = [f'Используется\n{cpu_usage:.1f}%', f'Свободно\n{cpu_free:.1f}%']
        self.cpu_ax.pie(cpu_data, labels=cpu_labels, colors=['#FF9999', '#66B2FF'],
                       autopct='%1.1f%%', startangle=90)
        self.cpu_ax.set_title('Загрузка CPU')

        # Обновляем график памяти
        memory_data = [memory_used, memory_free]
        memory_labels = [f'Используется\n{memory_used:.1f} ГБ', 
                        f'Свободно\n{memory_free:.1f} ГБ']
        self.memory_ax.pie(memory_data, labels=memory_labels, colors=['#99FF99', '#FFB366'],
                          autopct='%1.1f%%', startangle=90)
        self.memory_ax.set_title('Использование памяти')

        # Обновляем информацию о памяти
        self.memory_info.setText(
            f'Всего памяти: {memory_total:.1f} ГБ\n'
            f'Используется: {memory_used:.1f} ГБ\n'
            f'Свободно: {memory_free:.1f} ГБ'
        )

        # Обновляем график GPU и информацию
        if gpu_info:
            gpu_used = gpu_info['load']
            gpu_free = 100 - gpu_used
            gpu_data = [gpu_used, gpu_free]
            gpu_labels = [f'Используется\n{gpu_used:.1f}%', 
                         f'Свободно\n{gpu_free:.1f}%']
            self.gpu_ax.pie(gpu_data, labels=gpu_labels, colors=['#FF99FF', '#99FFFF'],
                           autopct='%1.1f%%', startangle=90)
            self.gpu_ax.set_title('Загрузка GPU')
            
            self.gpu_info.setText(
                f'GPU: {gpu_info["name"]}\n'
                f'Всего памяти: {gpu_info["memory_total"]:.1f} МБ\n'
                f'Используется: {gpu_info["memory_used"]:.1f} МБ'
            )
        else:
            self.gpu_ax.text(0.5, 0.5, 'GPU не найден', 
                           horizontalalignment='center', 
                           verticalalignment='center')
            self.gpu_info.setText('GPU информация недоступна')

        # Обновляем графики
        self.cpu_canvas.draw()
        self.memory_canvas.draw()
        self.gpu_canvas.draw()

def main():
    app = QApplication(sys.argv)
    window = SystemMonitorWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
