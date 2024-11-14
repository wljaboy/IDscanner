import os
from core.scanner import WaybillScanner
from PyQt6.QtWidgets import QApplication
from ui.main_ui import MainWindow
import sys

def main():
    """主程序"""
    print("启动程序...")
    
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        
        # 设置一些默认值
        window.min_length_input.setValue(10)  # YS号是10位
        window.max_length_input.setValue(10)
        window.uppercase_cb.setChecked(True)  # YS号包含大写字母
        window.digits_cb.setChecked(True)     # YS号包含数字
        window.prefix_input.setText("YS")     # YS号以YS开头
        
        # 显示窗口
        window.show()
        print("程序已启动，请在界面上进行操作")
        
        return app.exec()
        
    except Exception as e:
        print(f"程序启动出错: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 