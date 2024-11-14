import PyInstaller.__main__
import os
import sys
from pathlib import Path

def main():
    # 获取绝对路径
    current_dir = Path.cwd()
    icon_path = current_dir / 'ui' / 'icon.ico'
    
    if not icon_path.exists():
        print(f'错误: 找不到图标文件: {icon_path}')
        sys.exit(1)
    
    # 打包参数
    opts = [
        'main.py',
        '--name=IDscanner',
        '--onefile',
        '--windowed',
        '--clean',
        '--noconfirm',
        f'--icon={str(icon_path)}',              # 使用绝对路径指定图标
        '--version-file=version_info.txt',        # 添加版本信息
        '--add-data', './Tesseract-OCR;Tesseract-OCR',
        '--add-data', './dll;dll',
        '--add-binary', './dll/libzbar-64.dll;.',
    ]
    
    # 执行打包
    PyInstaller.__main__.run(opts)
    print('打包完成！')

if __name__ == '__main__':
    main()
