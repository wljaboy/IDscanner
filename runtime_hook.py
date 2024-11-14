import os
import sys
import shutil
from pathlib import Path

def setup_environment():
    if getattr(sys, 'frozen', False):
        # 获取可执行文件所在目录
        base_dir = Path(sys._MEIPASS)
        tesseract_dir = base_dir / 'Tesseract-OCR'
        
        # 确保 Tesseract 目录存在
        if tesseract_dir.exists():
            # 设置环境变量
            os.environ['PATH'] = str(tesseract_dir) + os.pathsep + os.environ.get('PATH', '')
            os.environ['TESSDATA_PREFIX'] = str(tesseract_dir / 'tessdata')
            
            print(f'Tesseract 路径: {tesseract_dir}')
            print(f'PATH: {os.environ["PATH"]}')
            print(f'TESSDATA_PREFIX: {os.environ["TESSDATA_PREFIX"]}')

setup_environment()
