"""
Physical Budgeting Module - 物理预算模块

论文核心要求：在调用LLM之前计算安全批次大小
防止LLM过度生成导致资源耗尽

功能：
1. 监控系统资源（RAM、磁盘、CPU）
2. 计算安全操作批次
3. 在LLM调用前锁定资源预算
"""

import psutil
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class BudgetResult:
    """预算计算结果"""
    total_ram_mb: int
    available_ram_mb: int
    safe_batch_size: int
    max_concurrent_operations: int
    estimated_time_per_batch: float
    total_batches_needed: int
    total_items: int
    safety_margin: float


class PhysicalBudget:
    """
    物理预算模块

    设计原则：
    - 在LLM调用前计算资源预算
    - 为每个操作分配资源上限
    - 如果资源不足，拒绝LLM调用或降低批次大小
    """

    # 安全常量
    RAM_SAFETY_MARGIN = 0.3  # 保留30% RAM给OS和其他进程
    MIN_RAM_PER_ITEM_MB = 50  # 每个文件/操作最少50MB
    MAX_BATCH_SIZE = 100  # 最大批次大小

    def __init__(self):
        self.system_profile = self._scan_system()

    def _scan_system(self) -> Dict[str, Any]:
        """扫描系统资源"""
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu = psutil.cpu_count()

        return {
            "total_ram_mb": mem.total // (1024 * 1024),
            "available_ram_mb": mem.available // (1024 * 1024),
            "total_disk_gb": disk.total // (1024 * 1024 * 1024),
            "free_disk_gb": disk.free // (1024 * 1024 * 1024),
            "cpu_cores": cpu
        }

    def compute_budget(self, total_items: int, item_size_mb: Optional[int] = None,
                       operation_type: str = "file_processing") -> BudgetResult:
        """
        计算安全预算

        Args:
            total_items: 总项目数（文件数、任务数等）
            item_size_mb: 每个项目平均大小（MB），None则使用默认值
            operation_type: 操作类型（影响资源估算）

        Returns:
            BudgetResult: 预算计算结果
        """
        # 获取当前可用资源
        mem = psutil.virtual_memory()
        available_ram_mb = mem.available // (1024 * 1024)

        # 计算安全可用RAM（扣除OS保留）
        safe_ram_mb = int(available_ram_mb * (1 - self.RAM_SAFETY_MARGIN))

        # 估算每个项目所需RAM
        if item_size_mb is None:
            item_size_mb = self.MIN_RAM_PER_ITEM_MB

        # 根据操作类型调整
        multiplier = {
            "file_processing": 2.0,  # 读取+处理
            "text_analysis": 1.5,      # 文本分析
            "image_processing": 5.0,  # 图像处理
            "video_processing": 10.0  # 视频处理
        }.get(operation_type, 2.0)

        ram_per_item = int(item_size_mb * multiplier)

        # 计算安全批次大小
        safe_batch_size = min(
            safe_ram_mb // ram_per_item,
            self.MAX_BATCH_SIZE,
            total_items
        )

        if safe_batch_size < 1:
            safe_batch_size = 1  # 至少处理1个

        # 计算总批次
        total_batches = (total_items + safe_batch_size - 1) // safe_batch_size

        # 估算每批时间（启发式）
        time_per_batch = {
            "file_processing": 2.0,
            "text_analysis": 1.0,
            "image_processing": 5.0,
            "video_processing": 30.0
        }.get(operation_type, 2.0)

        return BudgetResult(
            total_ram_mb=self.system_profile["total_ram_mb"],
            available_ram_mb=available_ram_mb,
            safe_batch_size=safe_batch_size,
            max_concurrent_operations=min(safe_batch_size, 10),
            estimated_time_per_batch=time_per_batch,
            total_batches_needed=total_batches,
            total_items=total_items,
            safety_margin=self.RAM_SAFETY_MARGIN
        )

    def check_llm_safety(self, budget: BudgetResult) -> Dict[str, Any]:
        """
        检查LLM调用是否安全

        如果资源不足，返回降级建议
        """
        if budget.safe_batch_size < 5:
            return {
                "safe": False,
                "warning": "资源极度紧张，建议暂停LLM调用",
                "suggestion": "关闭其他应用或增加内存",
                "fallback": "使用本地确定性策略，不调用LLM"
            }

        if budget.available_ram_mb < 500:
            return {
                "safe": False,
                "warning": "可用内存不足500MB，LLM调用可能失败",
                "suggestion": "降低批次大小或释放内存",
                "fallback": "batch_size=1, sequential_processing"
            }

        return {
            "safe": True,
            "warning": None,
            "suggestion": f"安全批次大小: {budget.safe_batch_size}",
            "fallback": None
        }

    def lock_budget(self, budget: BudgetResult) -> bool:
        """
        锁定资源预算

        在实际执行前，声明资源占用
        如果无法锁定，返回False
        """
        # 检查当前资源是否仍然满足预算
        mem = psutil.virtual_memory()
        available_mb = mem.available // (1024 * 1024)

        required_mb = budget.safe_batch_size * self.MIN_RAM_PER_ITEM_MB * 2

        if available_mb < required_mb:
            return False

        # 资源锁定成功（逻辑锁定，实际由OS管理）
        return True


# 便捷函数
def create_budget() -> PhysicalBudget:
    return PhysicalBudget()
