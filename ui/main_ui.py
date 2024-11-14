from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QLineEdit, QCheckBox, 
                            QProgressBar, QFileDialog, QGroupBox, QSpinBox,
                            QDialog, QDialogButtonBox, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen
import os
import shutil
from core.scanner import WaybillScanner
from PyQt6.QtWidgets import QApplication
from datetime import datetime

class RegionSelectDialog(QDialog):
    """识别区域选择对话框"""
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.selected_region = None
        self.start_pos = None
        self.current_pos = None
        
        self.setWindowTitle("选择识别区域")
        self.setMinimumSize(800, 600)
        
        # 加载图片
        self.pixmap = QPixmap(image_path)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 图片标签
        self.image_label = QLabel()
        self.image_label.setPixmap(self.pixmap)
        layout.addWidget(self.image_label)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # 设置鼠标跟踪
        self.image_label.setMouseTracking(True)
        self.image_label.mousePressEvent = self.mousePressEvent
        self.image_label.mouseMoveEvent = self.mouseMoveEvent
        self.image_label.mouseReleaseEvent = self.mouseReleaseEvent
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.pos()
            self.current_pos = event.pos()
            
    def mouseMoveEvent(self, event):
        if self.start_pos:
            self.current_pos = event.pos()
            self.update()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.start_pos:
            x1 = min(self.start_pos.x(), self.current_pos.x())
            y1 = min(self.start_pos.y(), self.current_pos.y())
            x2 = max(self.start_pos.x(), self.current_pos.x())
            y2 = max(self.start_pos.y(), self.current_pos.y())
            
            # 计算相对于图片的坐标比例
            img_width = self.pixmap.width()
            img_height = self.pixmap.height()
            
            self.selected_region = {
                'x1': x1 / img_width,
                'y1': y1 / img_height,
                'x2': x2 / img_width,
                'y2': y2 / img_height
            }
            
            self.start_pos = None
            self.current_pos = None
            self.update()
            
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.start_pos and self.current_pos:
            painter = QPainter(self)
            pen = QPen(QColor(255, 0, 0))
            pen.setWidth(2)
            painter.setPen(pen)
            
            x = min(self.start_pos.x(), self.current_pos.x())
            y = min(self.start_pos.y(), self.current_pos.y())
            w = abs(self.current_pos.x() - self.start_pos.x())
            h = abs(self.current_pos.y() - self.start_pos.y())
            
            painter.drawRect(x, y, w, h)

class MainWindow(QMainWindow):
    # 定义信号
    start_process_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("运单号识别工具")
        self.setMinimumSize(800, 600)
        
        # 存储选择的识别区域
        self.selected_region = None
        
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # === 识别设置组 ===
        recognition_group = QGroupBox("识别设置")
        recognition_layout = QVBoxLayout()
        
        # 识别方式
        method_layout = QHBoxLayout()
        self.barcode_cb = QCheckBox("条形码")
        self.qrcode_cb = QCheckBox("二维码")
        self.text_cb = QCheckBox("文字")
        method_layout.addWidget(self.barcode_cb)
        method_layout.addWidget(self.qrcode_cb)
        method_layout.addWidget(self.text_cb)
        recognition_layout.addLayout(method_layout)
        
        # 识别区域
        region_layout = QHBoxLayout()
        region_layout.addWidget(QLabel("识别区域:"))
        self.full_image_cb = QCheckBox("全图")
        self.full_image_cb.setChecked(True)
        self.custom_region_cb = QCheckBox("自定义区域")
        self.select_region_btn = QPushButton("选择区域")
        self.select_region_btn.setEnabled(False)
        
        region_layout.addWidget(self.full_image_cb)
        region_layout.addWidget(self.custom_region_cb)
        region_layout.addWidget(self.select_region_btn)
        recognition_layout.addLayout(region_layout)
        
        recognition_group.setLayout(recognition_layout)
        layout.addWidget(recognition_group)
        
        # === 运单号设置组 ===
        waybill_group = QGroupBox("运单号设置")
        waybill_layout = QVBoxLayout()
        
        # 运单号长度范围
        length_layout = QHBoxLayout()
        length_layout.addWidget(QLabel("运单号长度范围:"))
        self.min_length_input = QSpinBox()
        self.min_length_input.setMinimum(1)
        self.min_length_input.setMaximum(100)
        length_layout.addWidget(self.min_length_input)
        length_layout.addWidget(QLabel("至"))
        self.max_length_input = QSpinBox()
        self.max_length_input.setMinimum(1)
        self.max_length_input.setMaximum(100)
        length_layout.addWidget(self.max_length_input)
        waybill_layout.addLayout(length_layout)
        
        # 运单号字符构成
        chars_layout = QVBoxLayout()
        chars_layout.addWidget(QLabel("运单号字符构成:"))
        self.uppercase_cb = QCheckBox("大写字母 (A-Z)")
        self.lowercase_cb = QCheckBox("小写字母 (a-z)")
        self.digits_cb = QCheckBox("数字 (0-9)")
        self.custom_chars_layout = QHBoxLayout()
        self.custom_chars_layout.addWidget(QLabel("自定义字符:"))
        self.custom_chars_input = QLineEdit()
        self.custom_chars_layout.addWidget(self.custom_chars_input)
        
        chars_layout.addWidget(self.uppercase_cb)
        chars_layout.addWidget(self.lowercase_cb)
        chars_layout.addWidget(self.digits_cb)
        chars_layout.addLayout(self.custom_chars_layout)
        waybill_layout.addLayout(chars_layout)
        
        # 运单号特征
        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(QLabel("起始字符:"))
        self.prefix_input = QLineEdit()
        prefix_layout.addWidget(self.prefix_input)
        waybill_layout.addLayout(prefix_layout)
        
        suffix_layout = QHBoxLayout()
        suffix_layout.addWidget(QLabel("结束字符:"))
        self.suffix_input = QLineEdit()
        suffix_layout.addWidget(self.suffix_input)
        waybill_layout.addLayout(suffix_layout)
        
        waybill_group.setLayout(waybill_layout)
        layout.addWidget(waybill_group)
        
        # === 文件夹设置组 ===
        folder_group = QGroupBox("文件夹设置")
        folder_layout = QVBoxLayout()
        
        # 源文件夹
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("待处理文件夹:"))
        self.source_input = QLineEdit()
        self.source_btn = QPushButton("浏览")
        source_layout.addWidget(self.source_input)
        source_layout.addWidget(self.source_btn)
        folder_layout.addLayout(source_layout)
        
        # 目标文件夹
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("成功文件夹:"))
        self.target_input = QLineEdit()
        self.target_btn = QPushButton("浏览")
        target_layout.addWidget(self.target_input)
        target_layout.addWidget(self.target_btn)
        folder_layout.addLayout(target_layout)
        
        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)
        
        # === 进度显示 ===
        progress_group = QGroupBox("处理进度")
        progress_layout = QVBoxLayout()
        
        self.progress = QProgressBar()
        progress_layout.addWidget(self.progress)
        
        self.status_label = QLabel("待开始...")
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # === 控制按钮 ===
        self.start_btn = QPushButton("开始处理")
        layout.addWidget(self.start_btn)
        
        # 绑定事件
        self.setup_connections()
    
    def setup_connections(self):
        """设置信号连接"""
        self.source_btn.clicked.connect(self.select_source_folder)
        self.target_btn.clicked.connect(self.select_target_folder)
        self.start_btn.clicked.connect(self.start_process)
        self.full_image_cb.toggled.connect(self.toggle_region_selection)
        self.custom_region_cb.toggled.connect(self.toggle_region_selection)
        self.select_region_btn.clicked.connect(self.select_region)
    
    def select_source_folder(self):
        """选择源文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择待处理文件夹")
        if folder:
            self.source_input.setText(folder)
    
    def select_target_folder(self):
        """选择目标文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择成功文件夹")
        if folder:
            self.target_input.setText(folder)
    
    def toggle_region_selection(self, checked):
        """切换识别区域选择"""
        if self.sender() == self.full_image_cb and checked:
            self.custom_region_cb.setChecked(False)
            self.select_region_btn.setEnabled(False)
            self.selected_region = None
        elif self.sender() == self.custom_region_cb and checked:
            self.full_image_cb.setChecked(False)
            self.select_region_btn.setEnabled(True)
    
    def select_region(self):
        """选择识别区域"""
        if not self.source_input.text():
            QMessageBox.warning(self, "警告", "请先选择待处理文件夹！")
            return
            
        # 获取第一个图片文件
        image_files = [f for f in os.listdir(self.source_input.text()) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not image_files:
            QMessageBox.warning(self, "警告", "待处理文件夹中没有图片文件！")
            return
            
        image_path = os.path.join(self.source_input.text(), image_files[0])
        dialog = RegionSelectDialog(image_path, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.selected_region = dialog.selected_region
    
    def start_process(self):
        """开始处理按钮点击事件"""
        if not self.validate_inputs():
            return
        
        # 获取所有设置
        options = {
            'scan_barcode': self.barcode_cb.isChecked(),
            'scan_qrcode': self.qrcode_cb.isChecked(),
            'scan_text': self.text_cb.isChecked(),
            'min_length': self.min_length_input.value(),
            'max_length': self.max_length_input.value(),
            'uppercase': self.uppercase_cb.isChecked(),
            'lowercase': self.lowercase_cb.isChecked(),
            'digits': self.digits_cb.isChecked(),
            'custom_chars': self.custom_chars_input.text(),
            'prefix': self.prefix_input.text(),
            'suffix': self.suffix_input.text(),
            'region': self.selected_region if self.custom_region_cb.isChecked() else None
        }
        
        # 获取源文件夹和目标文件夹
        source_folder = self.source_input.text()
        target_folder = self.target_input.text()
        
        # 创建成功文件夹
        success_folder = os.path.join(target_folder, 'success')
        os.makedirs(success_folder, exist_ok=True)
        
        # 获取源文件夹中的图片文件
        image_files = [f for f in os.listdir(source_folder) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.pdf'))]
        
        if not image_files:
            QMessageBox.warning(self, "警告", "源文件夹中没有图片文件！")
            return
        
        # 创建扫描器实例
        try:
            scanner = WaybillScanner()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"初始化扫描器失败：{str(e)}")
            return
        
        # 禁用开始按钮
        self.start_btn.setEnabled(False)
        self.progress.setValue(0)
        
        # 处理每个图片
        success_count = 0
        failed_count = 0
        total = len(image_files)
        
        # 创建处理记录文件
        log_path = os.path.join(target_folder, 'process_log.txt')
        with open(log_path, 'w', encoding='utf-8') as log_file:
            log_file.write(f"处理时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_file.write("----------------------------------------\n")
            
            for i, image_file in enumerate(image_files, 1):
                try:
                    image_path = os.path.join(source_folder, image_file)
                    result = scanner.scan_image(image_path, options)
                    
                    if result:
                        # 构建新文件名
                        new_name = f"{result}{os.path.splitext(image_file)[1]}"
                        new_path = os.path.join(success_folder, new_name)
                        
                        # 移动文件到成功文件夹
                        shutil.move(image_path, new_path)
                        success_count += 1
                        
                        # 记录成功
                        log_file.write(f"成功 - {image_file} -> {new_name}\n")
                    else:
                        # 记录失败但不移动文件
                        failed_count += 1
                        log_file.write(f"失败 - {image_file} (未识别到运单号)\n")
                    
                    # 更新进度
                    self.progress.setValue(int(i * 100 / total))
                    self.status_label.setText(f"正在处理: {image_file} ({i}/{total})")
                    QApplication.processEvents()  # 保持界面响应
                    
                except Exception as e:
                    # 记录错误但不移动文件
                    failed_count += 1
                    log_file.write(f"错误 - {image_file} ({str(e)})\n")
                    QMessageBox.warning(self, "警告", f"处理文件 {image_file} 时出错：{str(e)}")
            
            # 写入统计信息
            log_file.write("\n----------------------------------------\n")
            log_file.write(f"处理完成！\n")
            log_file.write(f"总数：{total}\n")
            log_file.write(f"成功：{success_count}\n")
            log_file.write(f"失败：{failed_count}\n")
        
        # 启用开始按钮
        self.start_btn.setEnabled(True)
        
        # 显示结果
        QMessageBox.information(self, "完成", 
            f"处理完成！\n总数：{total}\n成功：{success_count}\n失败：{failed_count}\n\n"
            f"处理记录已保存到：{log_path}")
        
        self.status_label.setText("就绪")
        self.progress.setValue(100)
    
    def validate_inputs(self):
        """验证输入"""
        if not self.source_input.text() or not self.target_input.text():
            QMessageBox.warning(self, "警告", "请选择源文件夹和目标文件夹！")
            return False
        
        if not (self.barcode_cb.isChecked() or self.qrcode_cb.isChecked() or self.text_cb.isChecked()):
            QMessageBox.warning(self, "警告", "请至少选择一种识别方式！")
            return False
        
        if self.min_length_input.value() > self.max_length_input.value():
            QMessageBox.warning(self, "警告", "最小长度不能大于最大长度！")
            return False
        
        return True