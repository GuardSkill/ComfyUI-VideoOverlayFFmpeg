/**
 * ComfyUI Video Overlay Node - 前端预览支持
 * 
 * 将此文件保存为: ComfyUI/web/extensions/video_overlay_node.js
 */

import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

app.registerExtension({
    name: "VideoOverlayNode.Preview",
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "VideoOverlayNode") {
            
            // 在节点创建时添加视频预览widget
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                const result = onNodeCreated?.apply(this, arguments);
                
                // 创建视频预览容器
                this.videoWidget = this.addDOMWidget(
                    "video_preview",
                    "preview",
                    document.createElement("div")
                );
                
                this.videoWidget.element.style.width = "100%";
                this.videoWidget.element.style.minHeight = "200px";
                this.videoWidget.element.style.display = "flex";
                this.videoWidget.element.style.justifyContent = "center";
                this.videoWidget.element.style.alignItems = "center";
                this.videoWidget.element.style.backgroundColor = "#1a1a1a";
                this.videoWidget.element.style.borderRadius = "8px";
                this.videoWidget.element.style.padding = "10px";
                this.videoWidget.element.style.overflow = "hidden";
                this.videoWidget.element.style.boxSizing = "border-box";
                
                // 初始提示文本
                this.videoWidget.element.innerHTML = `
                    <div style="color: #888; text-align: center;">
                        <p>视频预览区域</p>
                        <p style="font-size: 12px;">执行后将显示生成的视频</p>
                    </div>
                `;
                
                return result;
            };
            
            // 处理执行结果，显示视频
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function(message) {
                onExecuted?.apply(this, arguments);
                
                if (message?.videos && message.videos.length > 0) {
                    const videoFilename = message.videos[0];
                    const videoUrl = api.apiURL(`/view?filename=${encodeURIComponent(videoFilename)}&type=output&subfolder=`);
                    
                    // 创建视频元素
                    this.videoWidget.element.innerHTML = `
                        <div style="width: 100%; max-width: 640px; display: flex; flex-direction: column; align-items: center;">
                            <video 
                                controls 
                                autoplay 
                                loop 
                                style="
                                    width: 100%; 
                                    height: auto;
                                    max-height: 400px;
                                    border-radius: 4px; 
                                    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                                    object-fit: contain;
                                    display: block;
                                "
                                src="${videoUrl}"
                            >
                                您的浏览器不支持视频标签
                            </video>
                            <div style="color: #aaa; font-size: 12px; margin-top: 8px; text-align: center; width: 100%;">
                                ${videoFilename}
                            </div>
                        </div>
                    `;
                    
                    console.log(`[VideoOverlay] 视频生成成功: ${videoFilename}`);
                }
            };
        }
    }
});