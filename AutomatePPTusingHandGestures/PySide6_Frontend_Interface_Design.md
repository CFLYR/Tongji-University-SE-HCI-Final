# PySide6 前端接口设计文档

## 核心后端接口类设计

### 1. PPT控制器接口 (PPTControllerInterface)

```python
class PPTControllerInterface:
    def __init__(self):
        self.ppt_controller = PPTController()
        self.is_presentation_active = False
        self.current_ppt_path = None
    
    # PPT文件操作
    def open_ppt_file(self, file_path: str) -> bool
    def close_presentation(self)
    def get_current_ppt_info(self) -> dict
    
    # 播放控制
    def start_presentation(self) -> bool
    def stop_presentation(self)
    def next_slide(self)
    def previous_slide(self)
    def jump_to_slide(self, slide_number: int)
    
    # 状态查询
    def is_active(self) -> bool
    def get_presentation_status(self) -> str
```

### 2. 手势检测控制接口 (GestureControlInterface)

```python
class GestureControlInterface:
    def __init__(self):
        self.gesture_detector = UnifiedGestureDetector()
        self.camera_active = False
        self.detection_active = False
        self.detection_interval = 0.1  # 默认100ms间隔
    
    # 检测控制
    def start_gesture_detection(self) -> bool
    def stop_gesture_detection(self)
    def pause_gesture_detection(self)
    def resume_gesture_detection(self)
    
    # 配置管理
    def set_detection_interval(self, interval: float)
    def get_detection_interval(self) -> float
    def is_detection_active(self) -> bool
    
    # 摄像头管理
    def initialize_camera(self, camera_id: int = 0) -> bool
    def release_camera(self)
    def get_camera_status(self) -> dict
```

### 3. 手势配置管理接口 (GestureConfigInterface)

```python
class GestureConfigInterface:
    def __init__(self):
        self.gesture_configs = {}
        self.config_file = "gesture_config.json"
    
    # 配置加载保存
    def load_configs(self) -> dict
    def save_configs(self) -> bool
    def reset_to_defaults(self)
    
    # 手势配置操作
    def get_gesture_config(self, gesture_name: str) -> dict
    def update_gesture_config(self, gesture_name: str, config: dict) -> bool
    def enable_gesture(self, gesture_name: str, enabled: bool)
    def get_all_gestures(self) -> list
    
    # 自定义手势
    def create_custom_gesture(self, name: str, config: dict) -> bool
    def delete_custom_gesture(self, name: str) -> bool
    def get_custom_gestures(self) -> list
```

### 4. 主控制器接口 (MainControllerInterface)

```python
class MainControllerInterface:
    def __init__(self):
        self.ppt_interface = PPTControllerInterface()
        self.gesture_interface = GestureControlInterface()
        self.config_interface = GestureConfigInterface()
        self.running = False
    
    # 系统控制
    def start_system(self) -> bool
    def stop_system(self)
    def is_system_running(self) -> bool
    def get_system_status(self) -> dict
    
    # 统计信息
    def get_fps(self) -> float
    def get_frame_count(self) -> int
    def get_runtime_stats(self) -> dict
```

## 前端界面要求

### 1. 主窗口布局

#### 顶部控制区域
- PPT文件选择按钮 (调用 `open_ppt_file`)
- 当前PPT文件显示标签
- 开始播放按钮 (调用 `start_presentation`)
- 结束播放按钮 (调用 `stop_presentation`)
- PPT状态指示器 (绿色=播放中, 红色=停止, 黄色=暂停)

#### 手势检测控制区域
- 开启手势检测按钮 (调用 `start_gesture_detection`)
- 关闭手势检测按钮 (调用 `stop_gesture_detection`)
- 检测状态指示灯 (绿色=检测中, 红色=已停止)
- 摄像头预览窗口 (可选)
- FPS显示标签

#### 检测间隔设置区域
- 滑动条控件 (范围: 50ms - 1000ms)
- 数值显示标签
- 应用按钮 (调用 `set_detection_interval`)

#### 手势配置管理区域
- 手势列表控件 (显示所有可用手势)
- 每个手势项包含:
  - 手势名称标签
  - 启用/禁用复选框
  - 置信度阈值滑动条
  - 持续时间设置数值框
  - 编辑按钮

### 2. 手势配置对话框

#### 基本设置
- 手势名称输入框
- 手势类型下拉框 (静态/动态/双手/持续)
- 对应动作下拉框 (下一页/上一页/暂停等)
- 启用复选框

#### 高级设置
- 置信度阈值滑动条 (0.0-1.0)
- 持续时间要求数值框 (秒)
- 手指模式配置 (仅静态手势)
- 运动模式选择 (仅动态手势)

#### 操作按钮
- 保存按钮 (调用 `update_gesture_config`)
- 取消按钮
- 测试按钮 (临时应用配置进行测试)
- 重置按钮 (恢复默认值)

### 3. 自定义手势管理

#### 创建新手势
- 手势录制按钮
- 录制进度指示器
- 录制说明文本
- 保存自定义手势按钮 (调用 `create_custom_gesture`)

#### 管理现有手势
- 自定义手势列表
- 删除按钮 (调用 `delete_custom_gesture`)
- 重新训练按钮
- 导入/导出按钮

### 4. 系统监控面板

#### 状态显示
- 系统运行状态
- 当前帧率
- 总处理帧数
- 运行时间
- 手势识别统计

#### 日志输出
- 滚动文本框显示系统日志
- 清除日志按钮
- 导出日志按钮

## 信号槽连接要求

### 核心信号定义
```python
# PPT控制相关信号
ppt_file_opened = Signal(str)
presentation_started = Signal()
presentation_stopped = Signal()
slide_changed = Signal(int)

# 手势检测相关信号
gesture_detection_started = Signal()
gesture_detection_stopped = Signal()
gesture_detected = Signal(str, float)  # 手势名称, 置信度
fps_updated = Signal(float)

# 配置相关信号
config_changed = Signal(str)  # 配置项名称
gesture_enabled = Signal(str, bool)  # 手势名称, 启用状态

# 系统状态信号
system_status_changed = Signal(str)
error_occurred = Signal(str)
```

### 槽函数要求
```python
# 界面更新槽函数
def update_ppt_status(self, status: str)
def update_gesture_status(self, active: bool)
def update_fps_display(self, fps: float)
def update_gesture_list(self)

# 用户操作响应槽函数
def on_ppt_file_selected(self)
def on_start_presentation_clicked(self)
def on_stop_presentation_clicked(self)
def on_gesture_detection_toggled(self, enabled: bool)
def on_detection_interval_changed(self, interval: float)
def on_gesture_config_changed(self, gesture_name: str)
```

## 数据验证要求

### 输入验证
- PPT文件路径有效性检查
- 检测间隔数值范围验证 (50-1000ms)
- 置信度阈值范围验证 (0.0-1.0)
- 持续时间范围验证 (0-10秒)
- 手势名称合法性检查

### 状态检查
- 系统初始化状态验证
- 摄像头可用性检查
- PPT软件运行状态验证
- 配置文件完整性检查

### 错误处理
- 摄像头连接失败处理
- PPT文件打开失败处理
- 配置保存失败处理
- 手势检测异常处理

