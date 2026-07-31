# OBS 录屏配置清单（CleanDoc 面试演示）

## 1. 安装 OBS
安装包已下载：`C:\Users\Administrator\Downloads\obs_installer.exe`（153MB，官方 32.2.1）
**操作**：双击运行 → 一路 Next → Finish。装完桌面会出现 OBS Studio 图标。

## 2. OBS 首次启动配置（向导）
首次启动会弹「自动配置向导」→ 直接**跳过**（Skip），手动配置更快。

## 3. 来源（Sources）添加
左下角「来源」面板 → 点 **+** → 选 **窗口采集（Window Capture）**：
- 窗口：选择 **Chrome / Edge**（含 localhost:8502 的窗口）
- 勾选「捕获光标（Capture cursor）」——演示时鼠标操作要录进去
- 确定后画面应显示浏览器内容

> 若窗口是「最大化」状态，OBS 会自适应，无需额外裁剪。

## 4. 音频（口播讲解要录）
右下角「混音器（Mixer）」：
- **桌面音频**：保留（录不到也没事，主要是口播）
- **麦克风/辅助音频**：确认有电平跳动（说话时）
- 若两个都没声音：菜单 文件→设置→音频→ 设备里选对麦克风

## 5. 录屏开始
- 点右下角「**开始录制**」（或快捷键 Ctrl+F5）
- 切到浏览器窗口开始演示
- 结束点「停止录制」（Ctrl+F5 再按一次）

## 6. 输出位置
默认在「视频」目录（`C:\Users\Administrator\Videos`），mp4 格式。
改位置：文件→设置→输出→录像路径。

## 7. 录前 Checklist（演示脚本 doc 里也有）
- [ ] `docker start archrag-neo4j` + `docker start cleandoc`
- [ ] 浏览器开 `http://localhost:8502`，**先手动生成一次**（预热模型 ~90s）
- [ ] 刷新页面回到初始表单
- [ ] **极光 VPN 已关**（或浏览器加 `--proxy-bypass-list="<-loopback>"`）——loopback 端口被代理劫持是已知坑，连不上 8502 先查这个
- [ ] OBS 窗口缩到最小（别挡住浏览器）

## 8. 演示完
- 停止录制 → 到 Videos 目录找到 mp4
- 可先自看一遍（对照演示脚本口播节奏）
