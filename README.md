# EduAI-Guard

面向高校学生的生成式 AI 学习使用伦理自查、风险解释与使用声明生成系统。

## 在线体验

已完成 VPS 在线部署，无需安装环境即可直接访问：

**[打开 EduAI-Guard 在线系统](https://shyeduai.dpdns.org/)**

在线版本可以直接体验调研数据概览、AI 使用伦理自查、八维风险画像、使用声明生成和自查报告下载等主要功能。如需审阅源代码、运行自动化测试或完整复现项目，请按照下方“本地运行”步骤操作。

## 项目简介

EduAI-Guard 将学术诚信、隐私保护、内容核查、透明披露等 AI 伦理原则转化为可操作的五步自查流程。系统使用本地确定性规则模型，从八个维度评估风险，并生成解释、修改建议、AI 使用声明和 Markdown 自查报告。

系统不调用外部大模型 API，不需要数据库。克隆仓库并安装依赖后即可在本地运行。

> 本系统用于学习与伦理自查，不是正式的学术诚信裁决工具。课程、学院和学校的明确规定始终具有更高优先级。

## 功能

- 调研数据概览：展示 79 份脱敏问卷的 AI 使用频率、用途和场景接受度。
- AI 使用伦理自查：通过五步向导收集具体学习任务中的 AI 使用情况。
- 八维风险画像：评估学术诚信、数据隐私、内容可靠、偏见公平、透明披露、学习主体、责任证据和版权授权风险。
- 风险解释与修改建议：展示触发规则及可执行的改进方向。
- AI 使用声明：生成适合附在作业中的透明披露文本。
- 自查报告下载：导出完整 Markdown 报告。
- 用户反馈：将反馈保存在本地 `data/feedback.csv`。

## 本地运行

建议使用 Python 3.10 或更高版本；项目已验证兼容 Python 3.9。

下载或克隆本仓库后，在项目根目录执行以下命令。

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Streamlit 通常会自动打开浏览器，也可以访问终端显示的本地地址。停止运行时，在终端按 `Ctrl+C`。

## 使用流程

1. 在“调研数据概览”查看脱敏问卷统计。
2. 进入“AI 使用伦理自查”，按照五步向导填写任务和 AI 使用情况。
3. 查看综合风险等级、八维画像、解释和修改建议。
4. 生成 AI 使用声明并下载 Markdown 自查报告。
5. 可在“用户反馈”页面提交体验意见。

## 风险维度

| 维度 | 关注问题 |
| --- | --- |
| 学术诚信 | AI 是否替代核心思考、论证、代码或实验过程 |
| 数据隐私 | 是否上传个人信息、同学资料或未公开材料 |
| 内容可靠 | 是否核查事实、引用、数据、公式和代码 |
| 偏见公平 | 工具差异、时间压力和训练不足是否影响公平 |
| 透明披露 | 是否主动说明 AI 使用范围 |
| 学习主体 | 是否仍能独立解释核心观点、代码和结论 |
| 责任证据 | 是否保留 prompt、草稿、修改与核查记录 |
| 版权授权 | 使用的资料、图片、论文和作品是否获得授权 |

综合风险采用最高风险优先原则，并对考试实质使用、生成实验数据、违反教师明确规定等行为设置特殊规则。具体实现见 [`rules.py`](rules.py)。

## 项目结构

```text
.
├── app.py                    # Streamlit 主程序
├── rules.py                  # 八维伦理风险规则
├── data_analyzer.py          # 调研 CSV 分析
├── statement_generator.py    # AI 使用声明生成
├── report_generator.py       # Markdown 自查报告生成
├── utils.py                  # 本地反馈与工具函数
├── requirements.txt          # 运行依赖
├── data/
│   └── metadata_sample.csv   # 79 份脱敏问卷样例
├── docs/
│   ├── project_document.md   # 项目设计与实现报告
│   ├── user_guide.md         # 详细使用说明
│   └── data_privacy.md       # 数据与隐私说明
└── tests/                    # 自动化测试
```

## 数据与隐私

公开仓库仅包含 `data/metadata_sample.csv` 脱敏样例。IP、UA、地理位置、答题时间和开放题原文均已移除。

用户提交的反馈会在首次提交时自动保存到本地 `data/feedback.csv`。该文件已加入 `.gitignore`。详细说明见 [`docs/data_privacy.md`](docs/data_privacy.md)。

## 可选反馈后台

反馈后台默认关闭，不影响系统其他功能。如需在本地查看反馈统计，可配置环境变量后启动：

```bash
export EDUAI_ADMIN_PASSWORD="设置一个管理密码"
python -m streamlit run app.py
```

Windows PowerShell 使用：

```powershell
$env:EDUAI_ADMIN_PASSWORD="设置一个管理密码"
python -m streamlit run app.py
```

也可以将 `.streamlit/secrets.toml.example` 复制为 `.streamlit/secrets.toml` 并修改密码。

## 测试

```bash
python -m unittest discover tests
python tests/check_streamlit_http.py
```

第一条命令验证规则、数据分析、报告和七个 Streamlit 页面；第二条命令会临时启动应用并检查首页与健康接口。

## 项目文档

- [`docs/project_document.md`](docs/project_document.md)：项目背景、需求分析、系统设计、实现、反馈与结论
- [`docs/user_guide.md`](docs/user_guide.md)：详细使用说明
- [`docs/data_privacy.md`](docs/data_privacy.md)：脱敏样例与本地反馈说明

## 开源许可

本项目使用 [MIT License](LICENSE) 开源。
