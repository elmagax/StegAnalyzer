import sys
import os
import time
import threading
from datetime import datetime
import http.server
import socketserver
import webbrowser
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFileDialog, QTextEdit, QDesktopWidget, 
                             QFrame, QProgressBar, QSplitter, QStatusBar, QMessageBox)
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QLinearGradient, QTextCharFormat, QTextCursor, QPixmap
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QUrl, pyqtSignal, QObject
import stegano
from stegano import lsb
import PyPDF2
import re
from PIL import Image
import html

class Communicate(QObject):
    update_progress = pyqtSignal(int)

class StegAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.communicate = Communicate()
        self.communicate.update_progress.connect(self.update_progress)
        self.initUI()

    def initUI(self):
        # Configuración de ventana
        self.setWindowTitle("StegAnalyzer Pro")
        self.setGeometry(100, 100, 1200, 800)
        self.center_window()
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, 
                    stop: 0 #0a1b2a, stop: 0.5 #1a2d4d, stop: 1 #0a1b2a);
                border: 2px solid #1e3a8a;
            }
            QLabel {
                color: #e0f7fa;
                font-family: 'Lato', 'Arial', sans-serif;
            }
            QPushButton {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, 
                    stop: 0 #3b82f6, stop: 1 #60a5fa);
                color: #0a1b2a;  /* Cambiado a un tono oscuro para mejor contraste */
                border: 2px solid #1e40af;
                padding: 10px 20px;
                border-radius: 12px;
                font-family: 'Lato', 'Arial', sans-serif;
                font-size: 14px;
                font-weight: bold;
                text-transform: uppercase;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, 
                    stop: 0 #2563eb, stop: 1 #3b82f6);
                border: 2px solid #1e3a8a;
                color: #0a1b2a;
            }
            QPushButton:pressed {
                background-color: #1e3a8a;
                color: #e0f7fa;
            }
            QTextEdit {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                    stop: 0 rgba(26, 45, 77, 0.9), stop: 1 rgba(10, 27, 42, 0.9));
                color: #e0f7fa;
                border: 2px solid #1e3a8a;
                border-radius: 10px;
                padding: 8px;
                font-family: 'Lato', 'Arial', sans-serif;
            }
            QFrame {
                border: 2px solid #1e3a8a;
                border-radius: 12px;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                    stop: 0 rgba(26, 45, 77, 0.8), stop: 1 rgba(10, 27, 42, 0.8));
            }
            QProgressBar {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                    stop: 0 #1a2d4d, stop: 1 #0a1b2a);
                border: 2px solid #1e3a8a;
                border-radius: 10px;
                text-align: center;
                color: #e0f7fa;
                font-family: 'Lato', 'Arial', sans-serif;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, 
                    stop: 0 #22d3ee, stop: 1 #06b6d4);
                border-radius: 5px;
            }
            QSplitter::handle {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, 
                    stop: 0 #1e3a8a, stop: 1 #2d4b8c);
                width: 6px;
                border-radius: 3px;
            }
            QStatusBar {
                background-color: #0a1b2a;
                color: #e0f7fa;
                font-family: 'Lato', 'Arial', sans-serif;
            }
        """)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Encabezado estilizado
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        logo_label = QLabel()
        logo_pixmap = QPixmap("logo.png")  # Reemplaza con tu logo
        if logo_pixmap.isNull():
            logo_label.setPixmap(QIcon.fromTheme("view-refresh").pixmap(60, 60))
        else:
            logo_label.setPixmap(logo_pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        title = QLabel("StegAnalyzer Pro")
        title.setFont(QFont("Lato", 30, QFont.Bold))
        title.setStyleSheet("color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop: 0 #e0f7fa, stop: 1 #a5f3fc);")
        header_layout.addWidget(logo_label)
        header_layout.addWidget(title)
        header_layout.addStretch()
        main_layout.addWidget(header_frame)

        # Botones
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setSpacing(15)
        self.upload_btn = QPushButton("Upload")
        self.upload_btn.setIcon(QIcon.fromTheme("document-open"))
        self.upload_btn.clicked.connect(self.upload_file)
        button_layout.addWidget(self.upload_btn)

        self.analyze_btn = QPushButton("Analyze")
        self.analyze_btn.setIcon(QIcon.fromTheme("system-run"))
        self.analyze_btn.clicked.connect(self.analyze_file)
        self.analyze_btn.setEnabled(False)
        button_layout.addWidget(self.analyze_btn)

        self.advanced_btn = QPushButton("Advanced")
        self.advanced_btn.setIcon(QIcon.fromTheme("preferences-system"))
        self.advanced_btn.clicked.connect(self.show_advanced)
        button_layout.addWidget(self.advanced_btn)

        self.view_report_btn = QPushButton("View Report")
        self.view_report_btn.setIcon(QIcon.fromTheme("document-preview"))
        self.view_report_btn.clicked.connect(self.view_report)
        button_layout.addWidget(self.view_report_btn)

        self.clear_logs_btn = QPushButton("Clear Logs")
        self.clear_logs_btn.setIcon(QIcon.fromTheme("edit-clear"))
        self.clear_logs_btn.clicked.connect(self.clear_logs)
        button_layout.addWidget(self.clear_logs_btn)

        self.stop_server_btn = QPushButton("Stop Server")
        self.stop_server_btn.setIcon(QIcon.fromTheme("process-stop"))
        self.stop_server_btn.clicked.connect(self.stop_server)
        self.stop_server_btn.setEnabled(False)
        button_layout.addWidget(self.stop_server_btn)

        button_layout.addStretch()
        main_layout.addWidget(button_frame)

        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setFormat("Analyzing... %p%")
        main_layout.addWidget(self.progress_bar)

        # Splitter para resultados y logs
        splitter = QSplitter(Qt.Vertical)
        splitter.setStyleSheet("QSplitter::handle { background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop: 0 #1e3a8a, stop: 1 #2d4b8c); width: 6px; border-radius: 3px; }")

        # Área de resultados
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        self.result_area.setPlaceholderText("Analysis results will appear here...")
        self.result_area.setMaximumHeight(150)
        splitter.addWidget(self.result_area)

        # Área de logs
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setPlaceholderText("Logs will appear here...")
        splitter.addWidget(self.log_area)
        splitter.setSizes([150, 450])
        main_layout.addWidget(splitter)

        # Barra de estado
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("QStatusBar { background-color: #0a1b2a; color: #e0f7fa; }")
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Version 1.0.7")

        # Pie de página
        footer_frame = QFrame()
        footer_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, 
                    stop: 0 #0a1b2a, stop: 1 #1a2d4d);
                border: 2px solid #1e3a8a;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        footer_layout = QHBoxLayout(footer_frame)
        footer_text = QLabel("© 2025 StegAnalyzer Pro | Developed by Thomas O'Neill Álvarez | <a href='https://github.com/ccyl13' style='color: #67e8f9;'>GitHub</a> | Version 1.0.7 | Licensed under MIT")
        footer_text.setOpenExternalLinks(True)
        footer_text.setAlignment(Qt.AlignCenter)
        footer_text.setStyleSheet("color: #a5f3fc; font-size: 16px; font-family: 'Lato', 'Arial', sans-serif; padding: 5px;")
        footer_layout.addWidget(footer_text)
        main_layout.addWidget(footer_frame)

        self.file_path = None
        self.analysis_results = {}
        self.server_thread = None
        self.server = None
        self.html_path = None
        self.progress = 0

    def center_window(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def log_message(self, message, color="white"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        format = QTextCharFormat()
        if color == "green":
            format.setForeground(QColor("#22d3ee"))
        elif color == "red":
            format.setForeground(QColor("#f87171"))
        else:
            format.setForeground(QColor("#e0f7fa"))

        cursor = self.log_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(formatted_message + "\n", format)
        self.log_area.setTextCursor(cursor)
        self.log_area.ensureCursorVisible()

    def clear_logs(self):
        self.log_area.clear()
        self.log_message("Logs cleared.")

    def view_report(self):
        if not self.analysis_results or not self.html_path:
            QMessageBox.warning(self, "No Data", "No analysis results to view. Please analyze a file first.")
            return

        PORT = 8000
        Handler = http.server.SimpleHTTPRequestHandler
        try:
            self.server = socketserver.TCPServer(("", PORT), Handler)
        except OSError as e:
            QMessageBox.critical(self, "Error", f"Failed to start server: {str(e)}. Port {PORT} might be in use.")
            return

        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.stop_server_btn.setEnabled(True)

        url = f"http://localhost:{PORT}/{os.path.basename(self.html_path)}"
        webbrowser.open(url)
        self.log_message(f"Report available at {url}", "green")
        self.status_bar.showMessage(f"Report served at {url}")

    def stop_server(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            if self.server_thread:
                self.server_thread.join()
            self.stop_server_btn.setEnabled(False)
            self.log_message("Server stopped.", "green")
            self.status_bar.showMessage("Server stopped")

    def generate_html_report(self):
        if not self.html_path:
            self.html_path = os.path.join(os.getcwd(), "report.html")

        try:
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StegAnalyzer Pro Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #0a1b2a; color: #e0f7fa; margin: 0; padding: 20px; }}
        .container {{ max-width: 900px; margin: auto; background: #1a2d4d; padding: 25px; border-radius: 15px; box-shadow: 0 0 15px rgba(34, 211, 238, 0.3); }}
        h1 {{ color: #3b82f6; text-align: center; text-transform: uppercase; }}
        h2 {{ color: #22d3ee; border-bottom: 2px solid #1e3a8a; padding-bottom: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 2px solid #1e3a8a; padding: 12px; text-align: left; }}
        th {{ background-color: #0a1b2a; }}
        .red {{ color: #f87171; }}
        .green {{ color: #22d3ee; }}
        .download-btn {{ background-color: #3b82f6; color: #ffffff; padding: 10px 20px; border: none; border-radius: 10px; cursor: pointer; text-decoration: none; }}
        .download-btn:hover {{ background-color: #2563eb; }}
        pre {{ max-height: 200px; overflow: auto; white-space: pre-wrap; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>StegAnalyzer Pro - Analysis Report</h1>
        <h2>Summary</h2>
        <p><strong>Date:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p><strong>File Analyzed:</strong> {html.escape(self.file_path or "Unknown")}</p>
        <h2>Results</h2>
        <table>
            <tr><th>Category</th><th>Details</th></tr>
            {self.analysis_results.get("results_table", "")}
        </table>
        <h2>Logs</h2>
        <pre>{html.escape(self.log_area.toPlainText().replace("\n", "<br>"))}</pre>
        <p><a href="{os.path.basename(self.html_path)}" download class="download-btn">Download Report</a></p>
    </div>
</body>
</html>
"""
            with open(self.html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.log_message(f"Report generated at {self.html_path}", "green")
        except Exception as e:
            self.log_message(f"Error generating HTML report: {str(e)}", "red")
            self.status_bar.showMessage("Error generating report")

    def upload_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "", 
                                                   "All Files (*);;Images (*.png *.jpg *.bmp);;Text Files (*.txt);;PDF Files (*.pdf)", 
                                                   options=options)
        if file_path:
            self.file_path = file_path
            self.result_area.setText(f"File selected: {file_path}")
            self.log_message(f"File uploaded: {file_path}")
            self.status_bar.showMessage(f"Selected: {os.path.basename(file_path)}")
            self.analyze_btn.setEnabled(True)
            self.analysis_results = {"file_path": file_path}

    def analyze_file(self):
        if not self.file_path:
            self.result_area.setText("No file selected!")
            self.log_message("No file selected!", "red")
            self.status_bar.showMessage("Error: No file selected")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.analyze_btn.setEnabled(False)
        self.log_message("Starting analysis...")
        self.status_bar.showMessage("Analyzing...")
        self.analysis_results["results_table"] = ""

        # Simulación de progreso con QTimer
        self.progress = 0
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: self.update_progress(self.progress + 1))
        self.timer.start(50)

    def update_progress(self, value):
        self.progress = value
        self.progress_bar.setValue(self.progress)
        if self.progress >= 100:
            self.timer.stop()
            self.perform_analysis()
            self.progress_bar.setVisible(False)
            self.analyze_btn.setEnabled(True)

    def perform_analysis(self):
        file_ext = os.path.splitext(self.file_path)[1].lower()
        self.result_area.clear()
        self.result_area.append("Analyzing file...\n")
        self.log_message(f"Analyzing file: {self.file_path}")
        results_table = ""

        try:
            if file_ext in [".png", ".jpg", ".bmp"]:
                try:
                    # Abrimos la imagen una vez para verificar
                    img = Image.open(self.file_path)
                    img.verify()  # Verifica la integridad de la imagen
                    img.close()

                    # Reabrimos la imagen para el análisis
                    img = Image.open(self.file_path)
                    if img.mode not in ['RGB', 'RGBA']:
                        img = img.convert('RGB')
                        temp_path = "temp_image.png"
                        img.save(temp_path)
                    else:
                        temp_path = self.file_path
                    img.close()
                except Exception as e:
                    self.result_area.append(f"Invalid image file: {str(e)}")
                    self.log_message(f"Invalid image file: {str(e)}", "red")
                    self.status_bar.showMessage("Error: Invalid image file")
                    results_table += f"<tr><td>Analysis Error</td><td class='red'>{html.escape(str(e))}</td></tr>"
                    self.analysis_results["results_table"] = results_table
                    self.generate_html_report()
                    return

                try:
                    hidden_data = lsb.reveal(temp_path)
                    if hidden_data:
                        self.result_area.append("Steganography detected!")
                        self.result_area.append(f"Hidden data: {hidden_data}")
                        self.log_message("Steganography detected! Hidden data found.", "red")
                        self.status_bar.showMessage("Steganography detected")
                        results_table += f"<tr><td>Steganography</td><td class='red'>Detected - Hidden data: {html.escape(hidden_data)}</td></tr>"
                    else:
                        self.result_area.append("No steganography detected in the image.")
                        self.log_message("No steganography detected in the image.", "green")
                        self.status_bar.showMessage("No steganography detected")
                        results_table += "<tr><td>Steganography</td><td class='green'>Not detected</td></tr>"
                except Exception as e:
                    self.result_area.append(f"Error analyzing image: {str(e)}")
                    self.log_message(f"Error analyzing image: {str(e)}", "red")
                    self.status_bar.showMessage("Error during image analysis")
                    results_table += f"<tr><td>Analysis Error</td><td class='red'>{html.escape(str(e))}</td></tr>"
                finally:
                    if 'temp_path' in locals() and temp_path != self.file_path and os.path.exists(temp_path):
                        os.remove(temp_path)

            elif file_ext == ".txt":
                try:
                    with open(self.file_path, 'rb') as f:  # Abrimos en modo binario para detectar caracteres ocultos
                        content = f.read()
                        # Buscamos caracteres no imprimibles (control characters)
                        if re.search(rb'[\x00-\x08\x0B\x0C\x0E-\x1F]', content):
                            self.result_area.append("Suspicious hidden characters detected!")
                            self.log_message("Suspicious hidden characters detected in text!", "red")
                            self.status_bar.showMessage("Suspicious characters detected")
                            results_table += "<tr><td>Hidden Characters</td><td class='red'>Detected</td></tr>"
                        else:
                            self.result_area.append("No obvious steganography detected in the text.")
                            self.log_message("No steganography detected in the text.", "green")
                            self.status_bar.showMessage("No steganography detected")
                            results_table += "<tr><td>Hidden Characters</td><td class='green'>Not detected</td></tr>"
                except Exception as e:
                    self.result_area.append(f"Error analyzing text file: {str(e)}")
                    self.log_message(f"Error analyzing text file: {str(e)}", "red")
                    self.status_bar.showMessage("Error during text analysis")
                    results_table += f"<tr><td>Analysis Error</td><td class='red'>{html.escape(str(e))}</td></tr>"

            elif file_ext == ".pdf":
                try:
                    with open(self.file_path, 'rb') as f:
                        pdf = PyPDF2.PdfReader(f)
                        if not hasattr(pdf, 'pages') or pdf.pages is None:
                            raise ValueError("Invalid PDF: No pages found.")
                        num_pages = len(pdf.pages)
                        if num_pages == 0:
                            raise ValueError("Invalid PDF: Empty document.")
                        text = ""
                        for page_num in range(num_pages):
                            page = pdf.pages[page_num]
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text
                        if re.search(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', text):
                            self.result_area.append("Suspicious hidden characters detected in PDF!")
                            self.log_message("Suspicious hidden characters detected in PDF!", "red")
                            self.status_bar.showMessage("Suspicious characters detected")
                            results_table += "<tr><td>Hidden Characters</td><td class='red'>Detected</td></tr>"
                        else:
                            self.result_area.append("No obvious steganography detected in the PDF.")
                            self.log_message("No steganography detected in the PDF.", "green")
                            self.status_bar.showMessage("No steganography detected")
                            results_table += "<tr><td>Hidden Characters</td><td class='green'>Not detected</td></tr>"
                except Exception as pdf_error:
                    self.result_area.append(f"Error processing PDF: {str(pdf_error)}")
                    self.log_message(f"Error processing PDF: {str(pdf_error)}", "red")
                    self.status_bar.showMessage("Error during PDF analysis")
                    results_table += f"<tr><td>Analysis Error</td><td class='red'>{html.escape(str(pdf_error))}</td></tr>"

            else:
                self.result_area.append("Unsupported file format!")
                self.log_message("Unsupported file format!", "red")
                self.status_bar.showMessage("Error: Unsupported file format")
                results_table += "<tr><td>Status</td><td class='red'>Unsupported file format</td></tr>"

            self.analysis_results["results_table"] = results_table
            self.generate_html_report()

        except Exception as e:
            self.result_area.append(f"Error during analysis: {str(e)}")
            self.log_message(f"Error during analysis: {str(e)}", "red")
            self.status_bar.showMessage("Error during analysis")
            self.analysis_results["results_table"] = f"<tr><td>Analysis Error</td><td class='red'>{html.escape(str(e))}</td></tr>"
            self.generate_html_report()

    def show_advanced(self):
        self.result_area.append("Advanced analysis feature coming soon!")
        self.log_message("Advanced analysis feature coming soon!")
        self.status_bar.showMessage("Advanced analysis coming soon")

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = StegAnalyzer()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
