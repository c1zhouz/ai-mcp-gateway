import asyncio
from datetime import datetime
from collections import deque

class LogManager:
    """
    业务日志管理器 (单例)
    用于捕获网关关键业务事件并通过 SSE 实时分发给前端。
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.queue = asyncio.Queue()
            # 存储最近 50 条日志，用于新连接时快速同步
            cls._instance.history = deque(maxlen=50)
        return cls._instance

    async def log(self, message: str, level: str = "INFO"):
        """
        上报一条新日志
        """
        log_entry = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": level,
            "message": message
        }
        
        # 保存到历史记录
        self.history.append(log_entry)
        
        # 放入分发队列
        await self.queue.put(log_entry)
        
        # 打印到控制台，确保 stdout 也有记录
        print(f"[{log_entry['time']}] {level}: {message}")

# 全局单例实例
log_manager = LogManager()
