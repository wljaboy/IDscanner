import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal
from ui.main_ui import MainWindow
from core.scanner import WaybillScanner
import shutil
import time

class ProcessThread(QThread):
    """处理线程"""
    progress_updated = pyqtSignal(int, int, str)  # 进度更新信号
    process_finished = pyqtSignal(int, int)  # 处理完成信号
    
    def __init__(self, source_folder, target_folder, scanner_options):
        super().__init__()
        self.source_folder = source_folder
        self.target_folder = target_folder
        self.scanner_options = scanner_options
        self.scanner = WaybillScanner()
        
    def run(self):
        # 获取所有图片文件
        image_files = [f for f in os.listdir(self.source_folder) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf'))]
        total = len(image_files)
        success_count = 0
        fail_count = 0
        
        for idx, filename in enumerate(image_files, 1):
            try:
                file_path = os.path.join(self.source_folder, filename)
                
                # 识别运单号
                waybill_number = self.scanner.scan_image(file_path, self.scanner_options)
                
                if waybill_number:
                    # 获取文件扩展名
                    _, ext = os.path.splitext(filename)
                    # 新文件名
                    new_filename = f"{waybill_number}{ext}"
                    new_path = os.path.join(self.target_folder, new_filename)
                    
                    # 移动并重命名文件
                    shutil.move(file_path, new_path)
                    success_count += 1
                else:
                    fail_count += 1
                
                # 发送进度信号
                self.progress_updated.emit(idx, total, filename)
                
            except Exception as e:
                fail_count += 1
                print(f"处理文件 {filename} 时出错: {str(e)}")
        
        # 发送完成信号
        self.process_finished.emit(success_count, fail_count)

class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = MainWindow()
        self.setup_connections()
        
    def setup_connections(self):
        """设置信号连接"""
        self.window.start_process_signal.connect(self.start_processing)
        
    def start_processing(self):
        """开始处理文件"""
        # 获取设置选项
        options = {
            'scan_barcode': self.window.barcode_cb.isChecked(),
            'scan_qrcode': self.window.qrcode_cb.isChecked(),
            'scan_text': self.window.text_cb.isChecked(),
            'min_length': self.window.min_length_input.value(),
            'max_length': self.window.max_length_input.value(),
            'uppercase': self.window.uppercase_cb.isChecked(),
            'lowercase': self.window.lowercase_cb.isChecked(),
            'digits': self.window.digits_cb.isChecked(),
            'custom_chars': self.window.custom_chars_input.text(),
            'prefix': self.window.prefix_input.text(),
            'suffix': self.window.suffix_input.text(),
            'region': self.window.selected_region if self.window.custom_region_cb.isChecked() else None
        }
        
        # 创建并启动处理线程
        self.process_thread = ProcessThread(
            self.window.source_input.text(),
            self.window.target_input.text(),
            options
        )
        
        # 连接信号
        self.process_thread.progress_updated.connect(self.update_progress)
        self.process_thread.process_finished.connect(self.process_finished)
        
        # 启动线程
        self.process_thread.start()
        
    def update_progress(self, current, total, filename):
        """更新进度显示"""
        percentage = int((current / total) * 100)
        self.window.progress.setValue(percentage)
        self.window.status_label.setText(f"正在处理: {filename} ({current}/{total})")
        
    def process_finished(self, success_count, fail_count):
        """处理完成"""
        self.window.start_btn.setEnabled(True)
        self.window.status_label.setText(
            f"处理完成！成功: {success_count} 失败: {fail_count}"
        )
        
    def run(self):
        """运行应用"""
        self.window.show()
        return self.app.exec()

if __name__ == '__main__':
    app = MainApp()
    sys.exit(app.run()) 