# 交互式大模型提示自动评估与修改框架

## 功能特性

- **交互式会话管理**：创建新会话或加载现有会话，方便跟踪提示的迭代过程。
- **多LLM支持（可配置）**：
    - **目标LLM**：用于执行用户提示并生成响应的模型（当前仅支持deepseek-chat模型）。
    - **评估LLM（可选）**：用于基于LLM的响应评估（“LLM作为裁判”）。
    - **修改助手LLM**：用于根据评估结果和当前提示生成修改建议。
- **自动响应评估**：
    - 支持基于规则的评估（例如，检测拒绝语）。
    - 支持基于LLM的评估，以获取更细致的反馈（如越狱成功度、详细度、安全性）。
- **LLM辅助的提示修改**：根据评估结果，智能建议提示的修改方案，旨在提高响应质量或达成特定目标（如绕过限制）。
- **交互流程**：用户可以处理当前提示、获取修改建议、接受建议、手动编辑提示或结束会话。
- **配置管理**：通过 `config.json` 文件管理API密钥和模型选择。
- **记忆功能**：交互历史和提示迭代过程保存在 `prompt_sessions` 目录下的JSON文件中。

## 项目结构

```
interactive_prompt_modifier/
├── core/                           # 核心逻辑模块
│   ├── __init__.py
│   ├── automatic_evaluator.py    # 自动评估模块
│   ├── llm_handler.py            # LLM API 交互模块
│   ├── main_controller.py        # 主控制器
│   ├── prompt_manager.py         # 提示与会话管理模块
│   └── prompt_modifier.py        # 提示修改模块
├── interfaces/                     # 用户接口模块
│   ├── __init__.py
│   └── cli.py                      # 命令行界面实现
├── utils/                          # 工具类模块
│   ├── __init__.py
│   └── config_manager.py         # 配置管理模块
├── prompt_sessions/                # (自动创建) 存储会话数据的目录
├── main.py                         # 应用主入口点
├── requirements.txt                # Python 依赖列表
├── config.json                     # (自动创建/需用户编辑) 配置文件，用于API密钥等
└── README.md                       # 本文档
```

## 安装与运行

1.  **下载项目**：将 `interactive_prompt_modifier` 文件夹保存到本地计算机。

2.  **安装依赖**：
    打开终端，进入项目根目录 (`interactive_prompt_modifier/`)，然后运行：
    ```bash
    pip install -r requirements.txt
    ```

3.  **配置API密钥**：
    - 项目首次运行时，会在根目录自动创建一个 `config.json` 文件。如果未自动创建，可以手动复制以下内容并保存为 `config.json`：
      ```json
      {
          
        "deepseek_api_key": "sk-e5ca96da010141e383134ca16f03b1cd",
        "deepseek_base_url": "https://api.deepseek.com/v1",
        "target_llm_model": "deepseek-chat",
        "judge_llm_model": "deepseek-chat",
        "modification_assistant_llm_model": "deepseek-chat",
        "evaluation_method": "rule_based"

      }
      ```
    - **重要**：将 `"YOUR_OPENAI_API_KEY_HERE"` 和 `"YOUR_GOOGLE_API_KEY_HERE"` 替换为有效API密钥。如果只使用其中一个服务，可以将另一个留空，但相应的功能将不可用。
    - 可以根据需要修改 `target_llm_model`（目标LLM）、`judge_llm_model`（评估LLM）、`modification_assistant_llm_model`（修改助手LLM）和 `evaluation_method`（评估方法，可选 `"rule_based"` 或 `"llm_judge"`）。

4.  **运行应用**：
    在项目根目录下，通过命令行运行：
    ```bash
    python main.py
    ```
    这将启动命令行交互界面。

## 使用方法

应用启动后，输入`python main.py`将看到主菜单，包含以下命令：

-   `new_session`: 开始一个新的提示评估与修改会话。
    -   系统会提示输入初始提示和可选的目标查询。
    -   创建成功后，会自动进入该会话的交互模式。
-   `load_session`: 加载一个之前保存的会话。
    -   可以输入会话ID，或从列出的可用会话中选择。
    -   加载成功后，会自动进入该会话的交互模式。
-   `list_sessions`: 列出所有已保存的会话及其基本信息。
-   `interact`: （通常在创建或加载会话后自动进入）进入指定会话的交互模式。
例如：`python main.py new_session`

### 会话交互模式

在会话交互模式中，可以执行以下操作：

1.  **Process current prompt with Target LLM**:
    -   将当前提示发送给配置的目标LLM。
    -   显示LLM的响应和自动评估结果。
2.  **Get modification suggestion (requires last response & evaluation)**:
    -   如果上一步已处理提示并得到响应和评估，此选项将调用修改助手LLM，根据当前提示、响应和评估结果生成一个修改后的提示建议。
    -   可以选择接受该建议（更新当前提示）或拒绝。
3.  **Manually edit current prompt**:
    -   允许直接在文本编辑器中修改当前提示。
4.  **View full session history**:
    -   显示当前会话的完整历史记录（JSON格式）。
5.  **End current session**:
    -   结束当前会话，并可标记其状态（如 completed, aborted）。
6.  **Exit interaction (back to main menu)**:
    -   退出当前会话的交互模式，返回到主命令菜单。




