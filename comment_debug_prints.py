  
 
"""
自动注释调试print语句脚本
"""

import os
import re
import glob

def comment_debug_prints(file_path):
    """注释掉文件中的调试print语句"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 匹配需要注释的print语句（包含调试标识）
        debug_patterns = [
            r'(\s*)print\(f?"🔧[^"]*"[^)]*\)',  # DEBUG标识
            r'(\s*)print\(f?"🔍[^"]*"[^)]*\)',  # DEBUG标识
            r'(\s*)print\(f?"✅[^"]*"[^)]*\)',  # 成功标识
            r'(\s*)print\(f?"❌[^"]*"[^)]*\)',  # 错误标识
            r'(\s*)print\(f?"⚠️[^"]*"[^)]*\)',  # 警告标识
            r'(\s*)print\(f?"ℹ️[^"]*"[^)]*\)',  # 信息标识
            r'(\s*)print\(f?"🎤[^"]*"[^)]*\)',  # 语音相关
            r'(\s*)print\(f?"🖐️[^"]*"[^)]*\)',  # 手势相关
            r'(\s*)print\(f?"🎬[^"]*"[^)]*\)',  # 录制相关
            r'(\s*)print\(f?"📊[^"]*"[^)]*\)',  # 状态相关
            r'(\s*)print\(f?"🕐[^"]*"[^)]*\)',  # 时间相关
            r'(\s*)print\(f?"📜[^"]*"[^)]*\)',  # 文稿相关
            r'(\s*)print\(f?"📍[^"]*"[^)]*\)',  # 位置相关
            r'(\s*)print\(f?"🔄[^"]*"[^)]*\)',  # 处理相关
            r'(\s*)print\(f?"🎯[^"]*"[^)]*\)',  # 目标相关
            r'(\s*)print\(f?"📺[^"]*"[^)]*\)',  # 显示相关
            r'(\s*)print\(f?"🖱️[^"]*"[^)]*\)',  # 鼠标相关
            r'(\s*)print\(f?"🧹[^"]*"[^)]*\)',  # 清理相关
            r'(\s*)print\(f?"⏰[^"]*"[^)]*\)',  # 定时器相关
            r'(\s*)print\(f?"🛑[^"]*"[^)]*\)',  # 停止相关
            r'(\s*)print\(f?"▶️[^"]*"[^)]*\)',  # 开始相关
            r'(\s*)print\(f?"⏹️[^"]*"[^)]*\)',  # 停止相关
            r'(\s*)print\(f?"💡[^"]*"[^)]*\)',  # 提示相关
            r'(\s*)print\(f?"📝[^"]*"[^)]*\)',  # 记录相关
            r'(\s*)print\(f?"🚀[^"]*"[^)]*\)',  # 启动相关
            r'(\s*)print\(f?"🔙[^"]*"[^)]*\)',  # 返回相关
            r'(\s*)print\(f?"🔜[^"]*"[^)]*\)',  # 前进相关
            r'(\s*)print\(f?"📂[^"]*"[^)]*\)',  # 文件相关
            r'(\s*)print\(f?"📦[^"]*"[^)]*\)',  # 包装相关
            r'(\s*)print\(f?"🎉[^"]*"[^)]*\)',  # 完成相关
            r'(\s*)print\(f?"🪟[^"]*"[^)]*\)',  # 窗口相关
        ]
        
        # 特殊的多行print语句处理
        special_patterns = [
            r'(\s*)print\("进入restore_window"\)',
            r'(\s*)print\("📦 悬浮窗已最小化"\)',
            r'(\s*)print\("✅ 窗口恢复完成，最小化按钮已正确恢复"\)',
            r'(\s*)print\("📂 悬浮窗已恢复"\)',
        ]
        
        # 应用所有模式
        for pattern in debug_patterns + special_patterns:
            content = re.sub(pattern, r'\1# print(', content)
        
        # 处理一些特殊的DEBUG标记
        content = re.sub(r'(\s*)print\("🔄 DEBUG:[^"]*"\)', r'\1# #print("🔄 DEBUG:', content)
        content = re.sub(r'(\s*)print\(f"🔍 DEBUG:[^"]*"\)', r'\1# print(f"🔍 DEBUG:', content)
        
        # 只有内容发生变化时才写入文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            #print(f"✅ 已处理: {file_path}")
            return True
        else:
            print(f"ℹ️ 无需处理: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ 处理文件失败 {file_path}: {e}")
        return False

def main():
    """主函数"""
    print("开始注释调试print语句...")
    
    # 查找所有Python文件
    python_files = glob.glob("*.py")
    
    # 排除这个脚本自己
    python_files = [f for f in python_files if f != "comment_debug_prints.py"]
    
    processed_count = 0
    
    for file_path in python_files:
        if comment_debug_prints(file_path):
            processed_count += 1
    
    print(f"\n处理完成！共处理了 {processed_count} 个文件")

if __name__ == "__main__":
    main()
