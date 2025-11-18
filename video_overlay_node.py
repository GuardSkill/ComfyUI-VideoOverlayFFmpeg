"""
ComfyUI Video Overlay Node
视频画中画合成节点

安装方法:
1. 将此文件放到 ComfyUI/custom_nodes/video_overlay_node.py
2. pip install ffmpeg-python
3. 确保系统已安装 ffmpeg

功能:
- 将小视频（带mask）叠加到大视频上
- 支持透明度调节
- 支持位置调节
- 自动处理时长差异
- 输出可预览的视频
"""

import os
import ffmpeg
import folder_paths
from pathlib import Path
import uuid


class VideoOverlayNode:
    """视频画中画合成节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "big_video_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                }),
                "small_video_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                }),
                "mask_video_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                }),
                "opacity": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "display": "slider",
                }),
                "position": (["right_bottom", "right_top", "left_bottom", "left_top", "center"], {
                    "default": "right_bottom"
                }),
                "margin_x": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 500,
                    "step": 1,
                }),
                "margin_y": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 500,
                    "step": 1,
                }),
                "h_size_ratio": ("FLOAT", {
                    "default": 0.25,
                    "min": 0.1,
                    "max": 1.0,
                    "step": 0.05,
                    "display": "slider",
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    FUNCTION = "overlay_videos"
    OUTPUT_NODE = True
    CATEGORY = "video"
    
    def get_video_info(self, video_path):
        """获取视频的时长和分辨率"""
        try:
            probe = ffmpeg.probe(video_path)
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            
            width = int(video_info['width'])
            height = int(video_info['height'])
            duration = float(probe['format']['duration'])
            
            return width, height, duration
        except Exception as e:
            raise ValueError(f"无法读取视频信息: {video_path}\n错误: {e}")
    
    def get_overlay_position(self, position, big_w, big_h, overlay_w, overlay_h, margin_x, margin_y):
        """根据位置参数计算overlay的x, y坐标"""
        positions = {
            "right_bottom": (f"main_w-overlay_w-{margin_x}", f"main_h-overlay_h-{margin_y}"),
            "right_top": (f"main_w-overlay_w-{margin_x}", str(margin_y)),
            "left_bottom": (str(margin_x), f"main_h-overlay_h-{margin_y}"),
            "left_top": (str(margin_x), str(margin_y)),
            "center": ("(main_w-overlay_w)/2", "(main_h-overlay_h)/2"),
        }
        return positions.get(position, positions["right_bottom"])
    
    def overlay_videos(self, big_video_path, small_video_path, mask_video_path, 
                      opacity, position, margin_x, margin_y, h_size_ratio):
        """执行视频合成"""
        
        # 检查文件是否存在
        for path in [big_video_path, small_video_path, mask_video_path]:
            if not os.path.exists(path):
                raise FileNotFoundError(f"文件不存在: {path}")
        
        # 获取视频信息
        print(f"[VideoOverlay] 正在分析视频信息...")
        big_w, big_h, big_dur = self.get_video_info(big_video_path)
        small_w, small_h, small_dur = self.get_video_info(small_video_path)
        
        print(f"[VideoOverlay] 大视频: {big_w}x{big_h}, {big_dur:.2f}秒")
        print(f"[VideoOverlay] 小视频: {small_w}x{small_h}, {small_dur:.2f}秒")
        
        # 计算小视频目标尺寸
        target_height = int(big_h * h_size_ratio)
        target_width = int(target_height * small_w / small_h)
        
        print(f"[VideoOverlay] 小视频目标尺寸: {target_width}x{target_height}")
        print(f"[VideoOverlay] 透明度: {opacity}, 位置: {position}")
        
        # 计算overlay位置
        overlay_x, overlay_y = self.get_overlay_position(
            position, big_w, big_h, target_width, target_height, margin_x, margin_y
        )
        
        # 生成输出文件路径
        output_dir = folder_paths.get_output_directory()
        unique_id = str(uuid.uuid4())[:8]
        output_filename = f"overlay_{unique_id}.mp4"
        output_path = os.path.join(output_dir, output_filename)
        
        # 加载输入视频
        big_input = ffmpeg.input(big_video_path)
        small_input = ffmpeg.input(small_video_path)
        mask_input = ffmpeg.input(mask_video_path)
        
        max_dur = max(big_dur, small_dur)
        
        try:
            if big_dur > small_dur:
                print(f"[VideoOverlay] 大视频更长，冻结小视频最后一帧")
                pad_dur = big_dur - small_dur
                
                # 延长小视频
                small_padded = ffmpeg.filter(
                    small_input.video,
                    'tpad',
                    stop_mode='clone',
                    stop_duration=pad_dur
                )
                
                # 延长mask
                mask_padded = ffmpeg.filter(
                    mask_input.video,
                    'tpad',
                    stop_mode='clone',
                    stop_duration=pad_dur
                )
                mask_gray = ffmpeg.filter(mask_padded, 'format', 'gray')
                
                # 缩放
                small_scaled = ffmpeg.filter(
                    small_padded,
                    'scale',
                    target_width,
                    target_height,
                    force_original_aspect_ratio='decrease'
                )
                mask_scaled = ffmpeg.filter(
                    mask_gray,
                    'scale',
                    target_width,
                    target_height,
                    force_original_aspect_ratio='decrease'
                )
                
                # 应用透明度到mask
                if opacity < 1.0:
                    mask_scaled = ffmpeg.filter(
                        mask_scaled,
                        'colorlevels',
                        romax=opacity
                    )
                
                # 合并alpha通道
                small_masked = ffmpeg.filter(
                    [small_scaled, mask_scaled],
                    'alphamerge'
                )
                
                # overlay
                video_out = ffmpeg.overlay(
                    big_input.video,
                    small_masked,
                    x=overlay_x,
                    y=overlay_y,
                    format='auto'
                )
                
                audio_out = small_input.audio
                
            else:
                print(f"[VideoOverlay] 小视频更长，循环大视频")
                
                # 循环大视频
                big_loop = ffmpeg.filter(
                    big_input.video,
                    'loop',
                    loop=-1,
                    size=32767,
                    start=0
                )
                
                # 处理mask
                mask_gray = ffmpeg.filter(mask_input.video, 'format', 'gray')
                
                # 缩放
                small_scaled = ffmpeg.filter(
                    small_input.video,
                    'scale',
                    target_width,
                    target_height,
                    force_original_aspect_ratio='decrease'
                )
                mask_scaled = ffmpeg.filter(
                    mask_gray,
                    'scale',
                    target_width,
                    target_height,
                    force_original_aspect_ratio='decrease'
                )
                
                # 应用透明度到mask
                if opacity < 1.0:
                    mask_scaled = ffmpeg.filter(
                        mask_scaled,
                        'colorlevels',
                        romax=opacity
                    )
                
                # 合并alpha通道
                small_masked = ffmpeg.filter(
                    [small_scaled, mask_scaled],
                    'alphamerge'
                )
                
                # overlay
                video_out = ffmpeg.overlay(
                    big_loop,
                    small_masked,
                    x=overlay_x,
                    y=overlay_y,
                    format='auto'
                )
                
                audio_out = small_input.audio
            
            # 输出
            print(f"[VideoOverlay] 开始合成视频...")
            output_stream = ffmpeg.output(
                video_out,
                audio_out,
                output_path,
                t=max_dur,
                vcodec='libx264',
                preset='medium',
                crf=23,
                acodec='aac',
                **{'movflags': '+faststart'}  # 启用流式播放
            )
            
            # 执行
            ffmpeg.run(output_stream, overwrite_output=True, capture_stderr=True, quiet=True)
            
            print(f"[VideoOverlay] ✓ 合成完成: {output_filename}")
            
            # 返回相对于output目录的路径，这样ComfyUI可以正确预览
            return {"ui": {"videos": [output_filename]}, "result": (output_path,)}
            
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
            print(f"[VideoOverlay] ✗ FFmpeg错误:\n{error_msg}")
            raise RuntimeError(f"视频合成失败: {error_msg}")
        except Exception as e:
            print(f"[VideoOverlay] ✗ 处理失败: {e}")
            raise


# ComfyUI节点注册
NODE_CLASS_MAPPINGS = {
    "VideoOverlayNode": VideoOverlayNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VideoOverlayNode": "Video Overlay (画中画合成)"
}