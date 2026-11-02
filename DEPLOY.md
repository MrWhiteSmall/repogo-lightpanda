# 固定版本、启动与系统边界

## 本期升级

2026-11-02改用官方固定版Lightpanda **1.0.2**，发行于2026-10-23。run.py锁定四种官方发行资产的SHA-256；摘要在执行前从官方GitHub发行API核对。固定页：https://github.com/lightpanda-io/browser/releases/tag/1.0.2 。此前nightly验证保留为历史记录，不冒充当前版本成绩。

固定版本减少滚动发行换包导致的下载变化，不能保证官方文件永远在线。每次执行仍校验摘要及version输出，变化时停止，不绕过校验。已有nightly缓存应先移到自己的历史备份目录，再运行；不要修改预期摘要强行接受旧缓存。

## 两条入口

Python3.9+，可写目录，首次联网下载官方文件。Mac ARM约89MiB。无pip依赖、无GPU、无Docker、无模型账号或API Key。

- 商品筛选：`bash start.sh`，成功显示“提取成功：2件”，查看`.runtime/results/latest/result.json`。
- 动态帮助页：`python3 export_help.py`，成功输出`.runtime/results/help/help.md`路径，内含三条问答。
- 手动预览商品页：`bash start.sh --serve-only`，常规浏览器打开当次终端地址，Ctrl+C停止。此模式不运行Lightpanda。

商品入口使用原生PandaScript操作；帮助入口使用官方`fetch --dump markdown --wait-selector`。Python包装负责下载、校验、临时服务与保存结果，不制造浏览器输出。遥测和核心转储在这些运行中关闭。没有使用外部商城、cookie、凭据、订单或交易。

每次普通任务结束自动关闭临时回环服务和浏览器进程；重新运行会开新端口。输入与保留结果需自行备份，同名`--output`目录会覆盖报告。帮助页自定义数据用`python3 export_help.py --data my-help.json --output my-help`。

## 对应系统实际结果

| 系统 | 本期状态 |
|---|---|
| macOS ARM64 | Python3.12.14，固定1.0.2商品4轮、帮助3轮全部通过 |
| shenji Linux x86_64 | Python3.10.12，Slurm226980，同7轮全部通过；0GPU |
| Intel Mac / Linux ARM64 | 有官方资产，本期未实跑 |
| Windows / WSL2 | 无原生Windows发行；已配置WSL2可参照Linux，但本期未实跑 |

Linux作业2026-11-02北京时间09:26:05—09:26:15，slurm-compute73，2CPU/2GiB/5分钟上限，未请求GPU。官方Linux文件在本机先下载校验，再同步至独立共享工作目录；计算节点冷下载未测。glibc的Linux包不代表musl/Alpine兼容。

商品4轮：预算100→2件、150→3件、手账改价68→108后100→1件、恢复原数据再启动→2件；帮助3轮：原始3条、改首条答案、新导出恢复原输入。均检查原输入未被覆盖、输出正确、临时端口关闭。

未验证任意第三方网站、登录验证码、模型/MCP/CDP集成、视觉截图一致性、性能倍数或云托管。修改上游、分发或对外托管另需核对AGPL义务。本仓库与附件不带上游程序、下载缓存和运行日志。

## 停止、备份、更新

普通命令会自动结束；若手工预览则Ctrl+C。备份你自己的catalog.json、help.json及需要保留的.runtime/results输出。重跑可使用不同--output名称避免覆盖。

升级另建目录，先查新发行、许可、资产摘要，完成商品与帮助场景验证后再迁移；不要把新版程序塞进旧缓存并沿用通过结论。当前脚本摘要不符时主动停止，是保护运行一致性而不是提示你跳过检查。
