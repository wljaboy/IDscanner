import cv2
import numpy as np
import pytesseract
from PIL import Image
import re
import os
import sys
import logging
from pyzbar.pyzbar import decode
import shutil

# 设置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class WaybillScanner:
    def __init__(self):
        logger.debug("初始化 WaybillScanner...")
        
        try:
            if getattr(sys, 'frozen', False):
                application_path = os.path.dirname(sys.executable)
            else:
                application_path = os.path.dirname(os.path.abspath(__file__))
                application_path = os.path.dirname(application_path)
            
            # 确保 DLL 文件在正确的位置
            dll_path = os.path.join(application_path, 'dll')
            os.makedirs(dll_path, exist_ok=True)
            
            # 复制 DLL 文件到系统临时目录
            temp_dir = os.path.join(os.environ['TEMP'], 'waybill_scanner_dll')
            os.makedirs(temp_dir, exist_ok=True)
            
            dlls = ['libiconv.dll', 'libzbar64.dll']
            for dll in dlls:
                src = os.path.join(dll_path, dll)
                dst = os.path.join(temp_dir, dll)
                if os.path.exists(src):
                    shutil.copy2(src, dst)
            
            # 添加 DLL 路径到环境变量
            if temp_dir not in os.environ['PATH']:
                os.environ['PATH'] = temp_dir + os.pathsep + os.environ['PATH']
                
            # 设置Tesseract路径
            tesseract_path = os.path.join(application_path, 'Tesseract-OCR', 'tesseract.exe')
            logger.debug(f"Tesseract 路径: {tesseract_path}")
            
            if not os.path.exists(tesseract_path):
                logger.error(f"Tesseract 执行文件不存在: {tesseract_path}")
                raise FileNotFoundError(f"找不到 Tesseract: {tesseract_path}")
                
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            logger.debug("初始化完成")
            
        except Exception as e:
            logger.error(f"初始化失败: {str(e)}")
            raise
    
    def scan_image(self, image_path, options):
        """扫描图片识别运单号"""
        logger.debug(f"开始扫描图片: {image_path}")
        logger.debug(f"扫描选项: {options}")
        
        results = []
        
        try:
            # 读取图片
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"无法读取图片: {image_path}")
                return None
            
            # 如果指定了识别区域，裁剪图片
            if options.get('region'):
                height, width = image.shape[:2]
                region = options['region']
                x1 = int(region['x1'] * width)
                y1 = int(region['y1'] * height)
                x2 = int(region['x2'] * width)
                y2 = int(region['y2'] * height)
                image = image[y1:y2, x1:x2]
            
            # 条形码/二维码识别
            if options['scan_barcode'] or options['scan_qrcode']:
                logger.debug("进行条码识别...")
                barcodes = decode(image)
                for barcode in barcodes:
                    data = barcode.data.decode('utf-8')
                    logger.debug(f"条码识别结果: {data}")
                    results.append(data)
            
            # 文字识别
            if options['scan_text']:
                logger.debug("进行文字识别...")
                
                # 预处理图像
                processed_image = self.preprocess_image(image)
                
                # OCR配置列表
                ocr_configs = [
                    {
                        'lang': 'chi_sim+eng',  # 中文+英文
                        'config': '--oem 3 --psm 3'  # 自动页面分割
                    },
                    {
                        'lang': 'chi_sim+eng',
                        'config': '--oem 3 --psm 6'  # 假设统一的文本块
                    },
                    {
                        'lang': 'eng',  # 仅英文模式可能对数字字母组合更准确
                        'config': '--oem 3 --psm 11'  # 稀疏文本
                    }
                ]
                
                # 运单号相关的关键词
                keywords = [
                    '运单', '单号', '快递单', '货运单', '订单号',
                    'NO', 'Number', '#', '编号', '号码',
                    '运输单', '提货单', '发货单'
                ]
                
                # 使用不同配置进行识别
                for config in ocr_configs:
                    text = pytesseract.image_to_string(
                        processed_image,
                        lang=config['lang'],
                        config=config['config']
                    )
                    
                    # 分行处理
                    lines = text.split('\n')
                    logger.debug(f"OCR配置 {config} 识别结果: {lines}")
                    
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # 1. 检查是否包含关键词
                        for keyword in keywords:
                            if keyword in line:
                                # 提取可能的运单号
                                # YS/YT开头的运单号
                                matches = re.findall(r'[YT][ST][0-9]{8,10}', line, re.IGNORECASE)
                                results.extend(matches)
                                
                                # 提取冒号或等号后面的数字字母组合
                                matches = re.findall(r'[:：=](.*?)(?=\s|$)', line)
                                for match in matches:
                                    # 清理提取的文本
                                    cleaned = re.sub(r'[^A-Z0-9]', '', match.upper())
                                    if cleaned and len(cleaned) >= 8:  # 假设运单号至少8位
                                        results.append(cleaned)
                        
                        # 2. 直接匹配可能的运单号格式（即使没有关键词）
                        # YS/YT开头的运单号
                        matches = re.findall(r'[YT][ST][0-9]{8,10}', line, re.IGNORECASE)
                        results.extend(matches)
                        
                        # 其他可能的运单号格式
                        matches = re.findall(r'[A-Z]{2}[0-9]{8,10}', line)
                        results.extend(matches)
                
                # 清理和标准化结果
                cleaned_results = []
                for result in results:
                    # 转换为大写
                    result = result.upper()
                    # 移除空白字符
                    result = ''.join(result.split())
                    # 移除特殊字符
                    result = re.sub(r'[^A-Z0-9]', '', result)
                    if result:
                        cleaned_results.append(result)
                
                # 去重
                results = list(dict.fromkeys(cleaned_results))
                logger.debug(f"文字识别最终结果: {results}")
            
            # 过滤结果
            filtered_results = self.filter_results(results, options)
            logger.debug(f"过滤后的结果: {filtered_results}")
            
            return filtered_results[0] if filtered_results else None
            
        except Exception as e:
            logger.error(f"扫描过程出错: {str(e)}")
            raise
    
    def filter_results(self, results, options):
        """过滤识别结果"""
        logger.debug(f"开始过滤结果: {results}")
        
        filtered = []
        min_length = int(options.get('min_length', 1))
        max_length = int(options.get('max_length', 100))
        prefix = options.get('prefix', '')
        suffix = options.get('suffix', '')
        
        # 构建允许的字符集
        allowed_chars = set()
        if options.get('uppercase'):
            allowed_chars.update(set('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
        if options.get('lowercase'):
            allowed_chars.update(set('abcdefghijklmnopqrstuvwxyz'))
        if options.get('digits'):
            allowed_chars.update(set('0123456789'))
        if options.get('custom_chars'):
            allowed_chars.update(set(options['custom_chars']))
        
        for result in results:
            if not result:
                continue
            
            result = result.strip()
            logger.debug(f"处理结果: {result}")
            
            # 检查长度
            if len(result) < min_length or len(result) > max_length:
                logger.debug(f"长度不在范围内: {len(result)} 不在 {min_length}-{max_length} 之间")
                continue
            
            # 检查字符构成
            if allowed_chars and not all(c in allowed_chars for c in result):
                logger.debug(f"包含不允许的字符")
                continue
            
            # 检查前缀
            if prefix and not result.startswith(prefix):
                logger.debug(f"前缀不匹配: {result} 不是以 {prefix} 开头")
                continue
            
            # 检查后缀
            if suffix and not result.endswith(suffix):
                logger.debug(f"后缀不匹配: {result} 不是以 {suffix} 结尾")
                continue
            
            logger.debug(f"找到匹配结果: {result}")
            filtered.append(result)
        
        return filtered
    
    def preprocess_image(self, image):
        """图像预处理以提高文字识别率"""
        try:
            # 转换为灰度图
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 自适应阈值处理
            binary = cv2.adaptiveThreshold(
                gray,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11,  # 邻域大小
                2    # 常数差值
            )
            
            # 降噪
            denoised = cv2.fastNlMeansDenoising(binary)
            
            # 增强对比度
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            
            return enhanced
            
        except Exception as e:
            logger.error(f"图像预处理失败: {str(e)}")
            return image