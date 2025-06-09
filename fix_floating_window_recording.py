# -*- coding: utf-8 -*-
"""
修复悬浮窗录制选项问题
Fix floating window recording option issue
"""

def fix_ppt_floating_window():
    """修复PPT悬浮窗中的录制选项问题"""
    
    # 读取当前文件
    with open('ppt_floating_window.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找并修复 show_config_dialog 方法
    old_method = '''    def show_config_dialog(self):
        """显示配置对话框"""
        if not RECORDING_AVAILABLE:
            print("❌ 录像功能不可用")
            return
            
        dialog = RecordingConfigDialog(self, self.recording_config)
        if dialog.exec() == QDialog.Accepted:
            self.recording_config = dialog.get_config()
            print("📝 录制配置已更新")'''
    
    new_method = '''    def show_config_dialog(self):
        """显示配置对话框"""
        if not RECORDING_AVAILABLE:
            print("❌ 录像功能不可用")
            return
            
        dialog = RecordingConfigDialog(self, self.recording_config)
        if dialog.exec() == QDialog.Accepted:
            self.recording_config = dialog.get_config()
            print("📝 录制配置已更新")
            print(f"🔍 新配置 - record_floating_window: {self.recording_config.record_floating_window}")
            
            # 立即更新录制助手的配置
            if self.recording_assistant:
                self.recording_assistant.config = self.recording_config
                print("✅ 录制助手配置已同步")'''
    
    if old_method in content:
        content = content.replace(old_method, new_method)
        print("✅ 已修复 show_config_dialog 方法")
    else:
        print("⚠️ 未找到 show_config_dialog 方法，可能已经修复")
    
    # 写回文件
    with open('ppt_floating_window.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("📝 修复完成")

def fix_video_recording_assistant():
    """修复视频录制助手中的配置问题"""
    
    # 读取当前文件
    with open('video_recording_assistant.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 确保调试信息足够详细
    old_debug = '''                print(f"🔍 DEBUG: record_floating_window = {self.config.record_floating_window}, floating_window = {self.floating_window is not None}")
                if not self.config.record_floating_window and self.floating_window:
                    print("🔧 正在遮盖悬浮窗区域...")
                    frame = self._mask_floating_window(frame)'''
    
    new_debug = '''                print(f"🔍 DEBUG: record_floating_window = {self.config.record_floating_window}, floating_window = {self.floating_window is not None}")
                if not self.config.record_floating_window and self.floating_window:
                    print("🔧 正在遮盖悬浮窗区域...")
                    frame = self._mask_floating_window(frame)
                elif self.config.record_floating_window:
                    print("✅ 录制悬浮窗内容，不进行遮盖")
                elif not self.floating_window:
                    print("ℹ️ 没有悬浮窗对象，跳过遮盖处理")'''
    
    if old_debug in content:
        content = content.replace(old_debug, new_debug)
        print("✅ 已增强调试信息")
    else:
        print("⚠️ 未找到对应的调试代码段")
    
    # 写回文件
    with open('video_recording_assistant.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("📝 修复完成")

if __name__ == "__main__":
    print("=== 修复悬浮窗录制选项问题 ===")
    fix_ppt_floating_window()
    fix_video_recording_assistant()
    print("=== 修复完成 ===")
    
    print("\n测试建议:")
    print("1. 运行 python test_floating_window_recording_simple.py")
    print("2. 观察控制台输出的调试信息")
    print("3. 在配置对话框中切换'录制悬浮窗内容'选项")
    print("4. 开始录制并检查是否有遮盖效果")
