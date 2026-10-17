from ultralytics import YOLO

# 加载预训练模型
model = YOLO('yolov8n.pt')

# 训练
results = model.train(
    data='datasets/automation.yaml',
    epochs=100,
    imgsz=640,
    batch=8,            # CPU 训练可设为 4 或 8
    device='cpu',       # 如果用 GPU 改为 'cuda:0'
    workers=0,          # Windows 下须设为 0 避免多进程问题
    augment=True,
    hsv_h=0.015,        # 色调增强，防止按钮颜色轻微变化影响
    hsv_s=0.7,          # 饱和度增强
    hsv_v=0.4,          # 明度增强
    scale=0.5,          # 缩放增强，让模型适应窗口大小变化
    translate=0.1,      # 平移增强
    mosaic=1.0,         # 马赛克增强
    fliplr=0.0,         # 左右翻转看需要（按钮可能不对称，建议关闭）
)



