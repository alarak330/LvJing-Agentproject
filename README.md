# 律镜-法律智能体类案报告生成系统 - 主程序使用说明

## 功能概述

这是一个基于GUI的法律智能体类案报告生成系统，支持：
- 上传Word文档（.doc, .docx）或PDF文档
- 输入用户问题或需求
- 自动生成Markdown格式的法律类案深度报告

## 系统架构

系统由以下智能体协作完成：

1. **ForumAgent（论坛智能体）** - 使用Qwen模型作为主持人，协调两个智能体进行辩论
2. **DataAnalysisAgent（数据分析智能体）** - 使用DeepSeek模型，分析用户需求并评估数据
3. **DataMiningAgent（数据挖掘智能体）** - 使用DeepSeek模型，搜索相关法律条文
4. **ReportAgent（报告生成智能体）** - 使用KIMI模型，生成最终报告

## 安装依赖

### 必需依赖

```bash
pip install python-docx PyPDF2 python-dotenv loguru langchain-openai
```

### 可选依赖（用于读取.doc文件）

**Windows系统：**
```bash
pip install pywin32
```

**Linux/Mac系统：**
```bash
# 需要安装 antiword 或 textract
pip install textract
```

## 环境变量配置

在项目根目录创建 `.env` 文件，配置以下环境变量：

```env
# DeepSeek API（用于 DataAnalysisAgent 和 DataMiningAgent）
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# Qwen API（用于 ForumAgent）
QWEN_API_KEY=your_qwen_api_key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# KIMI API（用于 ReportAgent）
KIMI_API_KEY=your_kimi_api_key
KIMI_BASE_URL=https://api.moonshot.cn/v1
```

## 使用方法

### 1. 启动程序

```bash
python main.py
```

### 2. 使用界面

1. **选择文件**：点击"浏览..."按钮，选择Word文档（.doc, .docx）或PDF文档
2. **输入问题**：在"问题输入"文本框中输入您的问题或需求
3. **生成报告**：点击"生成报告"按钮
4. **查看结果**：报告会显示在"报告结果"区域
5. **保存报告**：点击"保存报告"按钮，将报告保存为Markdown文件

### 3. 工作流程

```
用户上传文件 + 输入问题
    ↓
读取文件内容
    ↓
构建用户需求（文件内容 + 问题）
    ↓
ForumAgent 协调辩论
    ├─ DataAnalysisAgent 分析需求
    ├─ DataMiningAgent 搜索法律条文
    └─ 循环直到数据满足要求
    ↓
ReportAgent 生成报告
    ↓
格式化为 Markdown
    ↓
显示并保存报告
```

## 报告格式

生成的报告包含以下部分：

1. **需求概述** - 用户需求、案件类型、争议焦点、关键事实
2. **相关法律条文** - 法律名称、条号、条文内容、相关性分析、适用性
3. **数据分析** - 法律条文数量、数据质量、分析总结
4. **综合分析** - 对案件的综合分析
5. **建议** - 相关建议
6. **结论** - 最终结论

## 注意事项

1. **文件格式**：支持 `.doc`, `.docx`, `.pdf` 格式
2. **处理时间**：生成报告可能需要几分钟，请耐心等待
3. **网络连接**：需要稳定的网络连接以访问API
4. **API配额**：注意各API的调用配额限制

## 开发说明

### 项目结构

```
lvjing/
├── main.py                    # 主程序（GUI）
├── forum/                     # 论坛智能体
├── data analysis agent/       # 数据分析智能体
├── data mining agent/         # 数据挖掘智能体
├── report agent/              # 报告生成智能体
└── database/                  # 数据库连接（可选）
```

### 扩展功能

- 可以修改 `_format_to_markdown()` 方法自定义报告格式
- 可以调整各智能体的参数（模型名称、温度等）
- 可以添加数据库支持以存储历史报告



