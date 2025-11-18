# ComfyUI Video Overlay (FFmpeg)

基于 FFmpeg 的 ComfyUI 画中画合成节点。通过一条节点即可把带有 mask 的小视频叠加到主视频，支持透明度、位置与尺寸调节，并且自动处理不同长度的视频，还能在前端直接预览输出结果。

> English summary: Drop-in ComfyUI node that overlays a masked clip on top of a base clip using ffmpeg. It handles alpha masks, size/position, mismatched durations, and ships with a small web extension for instant previews.

---

## ✨ 功能亮点
- 纯 FFmpeg 流水线，合成结果无额外编解码器依赖
- 支持 mask/alpha 通道，透明度还可额外再调
- 可在五个常用锚点 + 自定义边距中定位小视频
- 自动对齐时长：小视频不足会自动补帧，主视频不足会自动循环
- 自动输出到 ComfyUI `output` 目录并推送前端预览

---

## 📦 依赖
1. **系统安装 FFmpeg**（命令行可执行）
2. `pip install ffmpeg-python`（已列在 `requirement.txt`）
3. ComfyUI 最新版（tested on ComfyUI 0.2+）

> ⚠️ 如果你使用便携版 ComfyUI，请确认 `python_embeded/python.exe` 能调用 `ffmpeg`。

---

## 🚀 安装步骤
1. 复制整个仓库到 `ComfyUI/custom_nodes/ComfyUI-VideoOverlayFFmpeg`
2. 安装依赖：`pip install -r requirement.txt`
3. （可选，但推荐）把 `web/video_overlay_node.js` 复制到 `ComfyUI/web/extensions/`，即可启用前端视频预览
4. 重启 ComfyUI

---

## 🔧 节点参数
| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `big_video_path` | STRING | 底图视频绝对路径或相对路径 |
| `small_video_path` | STRING | 叠加视频，通常是带透明背景或配合 mask 的人物 | 
| `mask_video_path` | STRING | 与小视频同分辨率/时长的灰度或透明度视频 |
| `opacity` | FLOAT 0~1 | 对 mask 追加整体透明度控制 |
| `position` | 枚举 | `right_bottom/right_top/left_bottom/left_top/center` |
| `margin_x` / `margin_y` | INT | 基于 position 的水平/垂直边距（像素） |
| `h_size_ratio` | FLOAT | 小视频目标高度 ÷ 主视频高度（默认 0.25） |

输出：`video_path`（STRING）——合成后的 MP4 文件路径，并同步到前端预览列表。

---

## 🧠 工作机制
1. **分析元数据**：读取主视频与小视频宽高、时长
2. **调整尺寸**：按 `h_size_ratio` 把小视频等比例缩放
3. **处理时长**  
   - 主视频更长 → `tpad` 克隆小视频与 mask 的最后一帧  
   - 小视频更长 → `loop` 方式循环主视频画面  
4. **合成透明度**：mask → 灰度 → `alphamerge`，再按需调节 `opacity`
5. **叠加**：使用 `ffmpeg.overlay` 按 position + margin 放置小视频
6. **封装输出**：`libx264 + aac`，带 `+faststart` 方便在线播放

---

## 🗂️ 示例流程
1. 使用 `Load Video` 节点读取主视频和小视频（或直接填路径）
2. 通过视频编辑工具提前导出小视频对应的 mask（黑白视频）
3. 配置本节点：  
   - `big_video_path`: `/data/base.mp4`  
   - `small_video_path`: `/data/portrait.mp4`  
   - `mask_video_path`: `/data/portrait_mask.mp4`  
   - `position`: `right_bottom`, `margin_x = 64`, `margin_y = 64`, `h_size_ratio = 0.3`
4. 执行图，等待终端提示 `[VideoOverlay] ✓`
5. 前端节点会自动显示输出视频；文件同时保存在 `ComfyUI/output/overlay_xxxx.mp4`

---

## ❓ 常见问题
- **报错 `文件不存在`**：确保路径无中文空格，或使用绝对路径  
- **没有预览**：确认已经把 `web/video_overlay_node.js` 放进 `ComfyUI/web/extensions/` 并重启  
- **ffmpeg command not found**：把 FFmpeg 加到系统 PATH，或在 ComfyUI 的启动脚本里导出 PATH  
- **透明度不生效**：检查 mask 是否正确（白色=不透明，黑色=全透明）  
- **输出颜色怪异**：请确保 mask 视频是灰度或单通道，必要时用 `format=gray` 重新导出

---

## 📮 反馈 & 计划
- 支持自定义输出编码器参数
- 增加可视化遮罩生成辅助节点
- 如有问题，欢迎在 Issues/PR 提交复现信息与日志

Enjoy ComfyUI Video Overlay! 🎬
