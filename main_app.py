import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QComboBox, QSpinBox, 
                             QLabel, QProgressBar, QTextEdit, QLineEdit)
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from qt_material import apply_stylesheet

import loop_generator

class Worker(QObject):
    finished = pyqtSignal(object, object)
    progress = pyqtSignal(str)

    def __init__(self, params):
        super().__init__()
        self.params = params

    def run(self):
        try:
            self.progress.emit("Iniciando geração...")
            
            folder_name, error = loop_generator.run_generation_process(
                style_to_generate=self.params['style'],
                bars=self.params['bars'],
                key=self.params['key'],
                scale=self.params['scale'],
                bpm=self.params['bpm'],
                progression_string=self.params['progression_string'],
                cover_title=self.params['cover_title'] # Passa o novo parâmetro
            )
            
            self.progress.emit("Processo finalizado!")
            if error:
                self.finished.emit(None, error)
            else:
                self.finished.emit(folder_name, None)
        except Exception as e:
            self.progress.emit(f"Ocorreu um erro crítico: {e}")
            self.finished.emit(None, str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Generator Loops Packs Python")
        self.setGeometry(100, 100, 500, 550) # Janela um pouco maior

        main_layout = QVBoxLayout()
        controls_layout = QVBoxLayout()
        
        # Seletor de Estilo
        self.style_combo = QComboBox()
        self.style_combo.addItems(['rock', 'funk', 'jazz', 'blues', 'reggae'])
        controls_layout.addWidget(QLabel("Gênero Musical:"))
        controls_layout.addWidget(self.style_combo)
        self.style_combo.currentTextChanged.connect(self.update_defaults)

        # Controles de Tonalidade e Escala
        key_layout = QHBoxLayout()
        self.key_combo = QComboBox()
        self.key_combo.addItems(['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'])
        self.scale_combo = QComboBox()
        self.scale_combo.addItems(['major', 'minor'])
        key_layout.addWidget(QLabel("Tonalidade:"))
        key_layout.addWidget(self.key_combo)
        key_layout.addWidget(QLabel("Escala:"))
        key_layout.addWidget(self.scale_combo)
        controls_layout.addLayout(key_layout)

        # Campo de Progressão
        controls_layout.addWidget(QLabel("Progressão de Acordes (ex: 1-minor, 4-major):"))
        self.progression_input = QLineEdit()
        controls_layout.addWidget(self.progression_input)

        # Campo para Título da Capa
        controls_layout.addWidget(QLabel("Nome da Capa (Título do Pack):"))
        self.cover_title_input = QLineEdit()
        self.cover_title_input.setPlaceholderText("Ex: Sunset Funk Grooves")
        controls_layout.addWidget(self.cover_title_input)

        # Controles de BPM e Compassos
        bpm_layout = QHBoxLayout()
        self.bpm_spinbox = QSpinBox()
        self.bpm_spinbox.setRange(40, 240)
        self.bars_spinbox = QSpinBox()
        self.bars_spinbox.setRange(2, 64)
        self.bars_spinbox.setSingleStep(2)
        bpm_layout.addWidget(QLabel("BPM:"))
        bpm_layout.addWidget(self.bpm_spinbox)
        bpm_layout.addWidget(QLabel("Compassos:"))
        bpm_layout.addWidget(self.bars_spinbox)
        controls_layout.addLayout(bpm_layout)

        main_layout.addLayout(controls_layout)
        main_layout.addStretch() # Adiciona espaço flexível

        self.generate_button = QPushButton("Gerar Loop Pack!")
        self.generate_button.clicked.connect(self.start_generation)
        main_layout.addWidget(self.generate_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.status_output = QTextEdit()
        self.status_output.setReadOnly(True)
        main_layout.addWidget(self.status_output)
        
        self.update_defaults(self.style_combo.currentText())

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def start_generation(self):
        self.generate_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_output.clear()

        params = {
            'style': self.style_combo.currentText(),
            'key': self.key_combo.currentText(),
            'scale': self.scale_combo.currentText(),
            'bpm': self.bpm_spinbox.value(),
            'bars': self.bars_spinbox.value(),
            'progression_string': self.progression_input.text(),
            'cover_title': self.cover_title_input.text() # Captura o novo título
        }

        self.thread = QThread()
        self.worker = Worker(params)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.update_status)
        self.worker.finished.connect(self.generation_finished)
        
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def update_status(self, message):
        self.status_output.append(message)

    def generation_finished(self, folder_name, error_message):
        self.progress_bar.setVisible(False)
        self.generate_button.setEnabled(True)

        if error_message:
            self.status_output.append(f"\nERRO:\n{error_message}")
        else:
            self.status_output.append(f"\nSUCESSO!\nLoop pack gerado na pasta:\n--> {folder_name}")

    def update_defaults(self, style):
        default_configs = {
            'rock': {'key': 'E', 'scale': 'minor', 'bpm': 140, 'bars': 8, 'prog': '1-minor, 6-major, 7-major, 5-major', 'title': 'Heavy Rock Riffs'},
            'funk': {'key': 'E', 'scale': 'minor', 'bpm': 110, 'bars': 4, 'prog': '1-minor, 4-minor, 5-dominant7, 1-minor', 'title': 'Electric Funk Jams'},
            'jazz': {'key': 'C', 'scale': 'major', 'bpm': 120, 'bars': 4, 'prog': '2-minor7, 5-dominant7, 1-major7, 1-major7', 'title': 'Late Night Jazz'},
            'blues': {'key': 'A', 'scale': 'major', 'bpm': 130, 'bars': 12, 'prog': 'Blues (progressão interna de 12 compassos)', 'title': 'Smoky Bar Blues'},
            'reggae': {'key': 'A', 'scale': 'minor', 'bpm': 70, 'bars': 4, 'prog': '1-minor, 1-minor, 4-minor, 4-minor', 'title': 'Island Riddims'}
        }
        
        config = default_configs.get(style)
        if config:
            self.key_combo.setCurrentText(config['key'])
            self.scale_combo.setCurrentText(config['scale'])
            self.bpm_spinbox.setValue(config['bpm'])
            self.bars_spinbox.setValue(config['bars'])
            self.progression_input.setText(config['prog'])
            self.cover_title_input.setText(config['title']) # Atualiza o novo campo de título
            
            is_blues = (style == 'blues')
            self.progression_input.setReadOnly(is_blues)
            self.key_combo.setEnabled(not is_blues)
            self.scale_combo.setEnabled(not is_blues)
            
        self.status_output.setText(f"Padrões para '{style.capitalize()}' carregados. Ajuste e clique em 'Gerar'.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_teal.xml')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())