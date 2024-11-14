运单号自动识别与重命名工具

项目简介

本项目旨在开发一款能够批量识别图片上运单号（包括条形码、二维码和文字形式）并据此重命名图片的工具。该工具支持多种运单号格式的识别，并提供灵活的配置选项以适应不同客户的特定需求。通过该工具，用户可以高效地管理大量物流单据的电子存档工作。

功能特性
运单号识别方式
支持条形码、二维码及文字三种运单号的识别方式，用户可根据实际需要选择一种或多种方式进行组合识别。
用户可自定义运单号的识别区域，适用于不同姿态（正置、倒置、左置、右置）的图片。
运单号特征配置
用户可设定运单号的长度范围以及构成字符集。
允许用户指定运单号的特殊特征，如开头或结尾特定字符，以便更精确地筛选出正确的运单号信息。
文件管理
用户可以分别设置待处理图片和处理后图片的存储路径。
成功处理的图片将被自动重命名并移至指定的目标文件夹；未能成功处理的图片保持在原始文件夹不变。
操作界面与用户体验
提供直观易用的图形化操作界面，无需编程知识即可轻松上手。
实时展示任务处理进度，包括已处理数量、总数量以及预估剩余时间。
处理完成后，给出详细的处理报告，包含成功和失败的数量统计。
技术栈
前端：使用Electron框架构建跨平台桌面应用，结合HTML/CSS/JavaScript实现图形用户界面。
后端：Python语言编写核心逻辑，利用OpenCV进行图像处理，Pytesseract用于OCR文本识别，ZBar或ZXing用于条形码和二维码识别。
打包：使用PyInstaller将Python脚本打包成可执行文件，确保非技术人员也能方便地运行本软件。
安装指南
下载最新版本的应用程序安装包。
双击安装包，按照提示完成安装过程。
启动应用程序，根据向导进行初始设置。
使用说明
打开应用程序，进入主界面。
在“设置”选项卡中，配置运单号识别参数、文件路径等信息。
点击“开始处理”，选择待处理的图片文件夹。
观察处理进度，等待任务完成。
查看处理结果，必要时对失败项进行手动校验。
贡献指南
欢迎任何形式的贡献，包括但不限于代码优化、新功能建议、文档改进等。请先阅读贡献者指南，了解如何有效地参与到项目中来。

希望这个项目能够帮助物流行业提高工作效率，减少人工错误。如果您有任何问题或建议，欢迎随时联系我！