# 🤖 大模型Agent数据生命周期管理系统

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.24%2B-red)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

一个现代化的大模型Agent数据生命周期管理平台，专为AI训练数据的全流程管理而设计。支持多项目管理、自定义Schema、智能数据过滤、AI驱动生成和可视化编辑等核心功能。

## ✨ 核心特性

### 🗂️ 项目管理
- **多项目支持**：独立管理不同Agent的训练数据
- **自定义Schema**：灵活定义Input和Result的JSON结构
- **配置隔离**：每个项目拥有独立的配置和数据空间
- **可视化统计**：直观的项目数据统计和分布图表
- **项目切换**：无缝在不同项目间切换工作

### 🔍 智能数据过滤
- **标签过滤**：基于内容标签的精确筛选
- **正则表达式**：强大的模式匹配和文本查找
- **LLM语义过滤**：利用大模型进行智能语义理解筛选
- **组合过滤**：支持多种过滤条件的灵活组合
- **实时预览**：过滤结果的即时可视化

### ✏️ 数据编辑与管理
- **可视化编辑**：直观的表格和表单编辑界面
- **字段验证**：自动JSON Schema验证
- **批量操作**：支持批量修改和删除
- **版本控制**：数据修改的自动备份
- **导入导出**：灵活的数据导入导出功能

### 🤖 AI驱动的数据生成
- **多种生成模式**：
  - Forward：根据Input生成Result
  - Backward：根据Result生成Input
  - Self-instruct：智能生成Input-Result对
- **智能提示词**：基于Schema自动生成优化的System Prompt
- **批量生成**：一次生成多条数据并逐一审核
- **质量控制**：支持编辑、保存或丢弃生成的数据
- **灵活保存**：可选择保存到训练集或验证集

### 📊 数据可视化
- **统计仪表板**：实时数据统计和分布图表
- **数据预览**：JSON数据的美化展示
- **进度跟踪**：数据处理进度的可视化
- **错误监控**：详细的错误信息和修复建议

## 🏗️ 系统架构

```
data_factory/
├── main.py                    # 主应用入口
├── data_manager.py            # 核心数据管理器
├── llm.py                     # 大模型接口
├── requirements.txt           # 项目依赖
├── pages/                     # 页面模块
│   ├── project_management.py  # 项目管理页面
│   ├── data_filter_modify.py  # 数据过滤修改页面
│   └── data_generation.py     # 数据生成页面
└── data/                      # 数据存储目录
    ├── 客服agent/           # 示例Agent项目
    │   ├── train_data.json    # 训练数据
    │   ├── val_data.json      # 验证数据
    │   ├── config.json        # 项目配置
    │   └── system_prompts/    # 系统提示词
    └── [project_name]/        # 其他项目...
```

## 🚀 快速开始

### 1. 环境准备

**Python要求**：Python 3.8+

**安装依赖**：
```bash
pip install -r requirements.txt
```

**依赖包说明**：
- `streamlit>=1.24.0` - Web界面框架
- `dashscope>=1.14.0` - 阿里云大模型API
- `pandas` - 数据处理
- `json` - JSON数据处理

### 2. 配置设置

**API密钥配置**：
```bash
# .env文件
echo "DASHSCOPE_API_KEY=your_dashscope_api_key" > .env
```

**支持的大模型**：
- `qwen-max` - 最强性能模型
- `qwen-turbo` - 平衡性能模型  
- `qwen-plus` - 高性价比模型

### 3. 启动应用

```bash
# 本地运行
nohup streamlit run main.py --server.headless true 
```

### 4. 开始使用

1. **创建项目**：在项目管理页面创建新的Agent项目
2. **定义Schema**：设计Input和Result的JSON结构
3. **数据管理**：导入、编辑或生成训练数据
4. **质量控制**：过滤、审核和优化数据质量

## 📖 功能详解

### 项目管理

**创建新项目**：
- 输入项目名称（支持中英文、数字、下划线）
- 定义Input Schema（JSON格式）
- 定义Result Schema（JSON格式）
- 自动创建项目目录和配置文件

**项目统计**：
- 训练数据数量和样例预览
- 验证数据数量和分布
- 项目配置信息展示
- 数据质量评估指标

### 数据过滤

**标签过滤示例**：
```json
// 过滤包含特定标签的数据
{
  "tags": ["video", "action", "detection"]
}
```

**正则表达式示例**：
```regex
// 匹配特定格式的文本
\b\w+_detection\b|action_\w+
```

**LLM语义过滤示例**：
```
// 自然语言描述的过滤条件
"找出所有关于视频动作检测的数据"
"筛选包含错误标注的训练样本"
```

### 数据生成

**Self-instruct模式**：
系统根据Schema自动生成提示词，指导大模型生成符合要求的训练数据。

**生成流程**：
1. 系统分析Input和Result Schema
2. 自动构建优化的System Prompt
3. 调用大模型生成多条数据
4. 解析并展示为可编辑的数据对
5. 逐一审核、编辑和保存

**质量控制**：
- 实时预览生成的原始内容
- 智能解析多个数据对
- 支持单独编辑每个数据对
- 可选择保存到训练集或验证集

## 🔧 高级配置

### 自定义Schema示例

**视频动作检测项目**：
```json
// Input Schema
{
  "type": "object",
  "properties": {
    "video_path": {"type": "string"},
    "frame_range": {"type": "array", "items": {"type": "integer"}},
    "detection_type": {"type": "string"}
  },
  "required": ["video_path", "detection_type"]
}

// Result Schema
{
  "type": "object", 
  "properties": {
    "actions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "action": {"type": "string"},
          "confidence": {"type": "number"},
          "bbox": {"type": "array", "items": {"type": "number"}}
        }
      }
    }
  }
}
```

### 大模型配置

**模型选择建议**：
- **qwen-max**：复杂推理任务，高质量数据生成
- **qwen-turbo**：平衡性能，适合批量处理
- **qwen-plus**：成本敏感场景，基础数据生成


## 📊 数据格式规范

### 训练数据格式
```json
[
  {
    "Input": {
      // 根据项目Schema定义的输入数据
    },
    "Result": {
      // 根据项目Schema定义的输出数据  
    }
  }
]
```

### 项目配置格式
```json
{
  "project_name": "项目名称",
  "input_schema": {...},
  "result_schema": {...},
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

## 🛠️ 开发指南

### 扩展新功能

**添加新的过滤方式**：
1. 在`data_manager.py`中添加过滤方法
2. 在`pages/data_filter_modify.py`中添加UI组件
3. 更新过滤逻辑的调用接口

**添加新的数据生成模式**：
1. 在`data_manager.py`中实现生成方法
2. 在`pages/data_generation.py`中添加UI选项
3. 配置相应的System Prompt模板

## 📋 TODO

### ✅ 已完成功能
- **SELF-INSTRUCT模式**：智能生成Input-Result数据对，系统自动构建优化的System Prompt并生成符合Schema要求的训练数据

### 🚧 待开发功能
- **Forward模式**：用于补充常规样本
  - 根据给定的Input生成对应的Result
  - 适用于已有输入数据，需要生成标准输出的场景
  - 支持批量处理和质量审核
  
- **Backward模式**：专门针对Agent薄弱的输出结果反推输入
  - 根据期望的Result反推生成对应的Input
  - 针对Agent表现不佳的场景，通过逆向工程强化训练数据
  - 帮助识别和补充Agent的薄弱环节

- **合成数据的LLM质量过滤**

## 🔍 故障排除

### 常见问题

**1. API密钥错误**
```
错误：unauthorized
解决：检查DASHSCOPE_API_KEY是否正确设置
```

**2. Schema验证失败**
```
错误：Schema格式错误
解决：确保JSON Schema语法正确，使用在线验证工具检查
```

## 📄 许可证

本项目采用MIT许可证 - 详见 [LICENSE](LICENSE) 文件

---

<div align="center">

**🤖 大模型Agent数据生命周期管理系统 v1.0.0**

*让AI数据管理更简单、更智能、更高效*

</div>