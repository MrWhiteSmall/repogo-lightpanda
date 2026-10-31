# 系统入口、固定快照与工作机制

## 支持与实测分开记录

| 系统 | 上游发行形式 | 本轮情况 | 入口 |
|---|---|---|---|
| macOS Apple Silicon | aarch64-macos | 已实测四轮动态筛选和提取，Python 3.9.6 | `bash start.sh` 或 `bash start.command` |
| macOS Intel | x86_64-macos | 官方包与摘要已整理，未实测 | `bash start.sh` |
| Linux x64 | x86_64-linux，glibc | shenji Slurm 四轮动态筛选/提取和端口关闭通过；Python 3.10.12 | `bash start.sh` |
| Linux ARM64 | aarch64-linux，glibc | 官方包与摘要已整理，未实测 | `bash start.sh` |
| Windows | 无原生包，官方建议 WSL2 | WSL2 未实测；Windows ARM/仿真均不据此通过 | 已有 WSL2 内运行 `bash start.sh` |

Alpine/musl、Android/Termux 不属于这些 glibc Linux 包的直接适用对象。入口不会自动修改执行策略、安装 WSL、启动虚拟机或改系统设置。Mac 解压后双击 `.command` 的体验受本机终端和文件权限影响，保底使用终端 `bash start.sh`。

上游固定快照版本：`1.1.0-nightly.11423+56980afde`。官方 nightly 下载页 https://github.com/lightpanda-io/browser/releases/tag/nightly ，本次资产观察日期 2026-11-01（北京时间），资产更新时间为 2026-10-31。四架构摘要在 `run.py` ASSETS 中，来自该页，不是从任意下载包反向补填。Mac ARM SHA-256：

```text
273a4659510f8c48e6c5f26a2eee6aa20051632210cbf0f59975ac705056c44f
```

该页旧 nightly 标签指向的 `8ec22ca...` 是历史标签，不是本次二进制构建提交证明。版本后缀记录的是二进制自己报告的构建标识，本期未核实其完整源码提交。未来滚动文件摘要不符会失败关闭，不能称永久复现；需要重新核验版本、摘要、功能后发布新的包，不能只改摘要放行。

## 运行链路

Python 标准库把 `site/index.html` 与本次指定商品数据暴露在一个仅 `127.0.0.1` 的临时随机端口；别的路径返回 404。HTML 初始没有商品行，页面通过 `fetch('/catalog.json')` 读取数据，用 JavaScript 创建 6 行商品。筛选按钮的页面事件处理器按分类、预算和库存重新生成行。

Lightpanda 用官方 native PandaScript：`new Page()` → `goto` → `waitForScript` 等状态为 ready → `selectOption` 选分类 → `fill` 填预算 → `click` 触发页面事件 → `extract` 按 CSS 选择器取字段。CSS 选择器在这里是定位页面元素的规则，例如 `.product .price` 表示每条商品行中的价格。

Python 负责启动服务、校验下载、保存报告、比较输入输出与关闭进程；页面负责筛选；Lightpanda 负责执行页面脚本、派发交互事件与提取 DOM（浏览器里的文档结构）。因此不会把 Python 自己算出的筛选列表冒充浏览器提取结果。

本期使用固定脚本，不调用模型。官方还提供 CDP、MCP、Agent 模式，未在本轮验证。它没有传统完整图形渲染引擎，其截图是文字布局输出，不适合拿来证明网页视觉一致。文档页面图是 Edge 对同一原创练习的展示，和 Lightpanda 的 JSON 证据分开。

上游默认有遥测。本入口每次设置 `LIGHTPANDA_DISABLE_TELEMETRY=true`、`LIGHTPANDA_DISABLE_CORE_DUMP=1`，不导入个人浏览器资料、不加载 Cookie、不使用平台登录与 API 凭据。首次下载官方文件仍需联网，本地核心练习不访问第三方网站。不能把本样例成功推广为任意网站、验证码或登录流程都兼容。

## Linux 独立补测（2026-11-01）

Slurm 作业 224656，节点 slurm-compute73，slurm-2080ti 分区申请 2 CPU、2GB 内存，未申请/使用 GPU。02:28:27–02:28:32（北京时间），官方 Linux x64 二进制同版本、SHA-256 为 `19f3fee25fb14bb75a1e0c1e0f8ab9cce842950544e4a144fbad3884c94b98a3`。100/150预算、手账改价、恢复原数据重启四轮及端口关闭均通过。服务器直连官方下载过慢，改为本机从官方下载并校验后同步到独立共享目录，计算节点首次冷下载未测；不因此宣称在任何Linux上可无障碍下载。未修改其他作业或使用已有GPU。
