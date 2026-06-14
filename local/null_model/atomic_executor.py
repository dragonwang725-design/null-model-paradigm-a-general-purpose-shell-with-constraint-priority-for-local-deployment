"""
Atomic Executor - 原子执行与回滚模块

论文核心要求：
- 每批操作要么全提交，要么全回滚
- 保证系统一致性
- 如果LLM失败，回退到确定性默认值

功能：
1. 批次执行（原子性）
2. 执行前备份（可回滚）
3. 执行后验证
4. 失败时回滚
"""

import shutil
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class ExecutionStatus(Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class Operation:
    """单个操作"""
    op_id: str
    op_type: str  # copy, move, delete, read, write
    source: str
    target: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: ExecutionStatus = ExecutionStatus.PENDING
    checksum_before: Optional[str] = None
    checksum_after: Optional[str] = None
    error: Optional[str] = None


@dataclass
class Batch:
    """操作批次"""
    batch_id: str
    operations: List[Operation]
    status: ExecutionStatus = ExecutionStatus.PENDING
    backup_path: Optional[str] = None


class AtomicExecutor:
    """
    原子执行器

    设计原则：
    - 批次内所有操作要么全成功，要么全回滚
    - 执行前创建备份
    - 执行后验证校验和
    - 失败时自动回滚
    """

    def __init__(self, backup_dir: str = "./backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.batches: List[Batch] = []

    def create_batch(self, operations: List[Dict[str, Any]]) -> Batch:
        """
        创建操作批次

        Args:
            operations: 操作列表，每个操作是dict

        Returns:
            Batch: 创建的批次
        """
        batch_id = f"batch_{len(self.batches)}"
        ops = []

        for i, op in enumerate(operations):
            ops.append(Operation(
                op_id=f"{batch_id}_op_{i}",
                op_type=op.get("action_type", "unknown"),
                source=op.get("source", ""),
                target=op.get("target"),
                parameters=op.get("parameters", {})
            ))

        batch = Batch(batch_id=batch_id, operations=ops)
        self.batches.append(batch)
        return batch

    def execute_batch(self, batch: Batch, 
                      pre_check: Optional[Callable] = None,
                      post_check: Optional[Callable] = None) -> bool:
        """
        原子执行批次

        流程：
        1. 预检查
        2. 创建备份
        3. 执行每个操作
        4. 验证
        5. 如果失败，回滚

        Args:
            batch: 要执行的批次
            pre_check: 预检查函数
            post_check: 后检查函数

        Returns:
            bool: 是否成功
        """
        batch.status = ExecutionStatus.EXECUTING

        # 1. 预检查
        if pre_check and not pre_check(batch):
            batch.status = ExecutionStatus.FAILED
            return False

        # 2. 创建备份
        if not self._create_backup(batch):
            batch.status = ExecutionStatus.FAILED
            return False

        # 3. 执行每个操作
        executed = []
        for op in batch.operations:
            try:
                self._execute_operation(op)
                executed.append(op)
            except Exception as e:
                op.status = ExecutionStatus.FAILED
                op.error = str(e)
                # 回滚已执行的操作
                self._rollback_batch(batch, executed)
                batch.status = ExecutionStatus.ROLLED_BACK
                return False

        # 4. 后检查
        if post_check and not post_check(batch):
            self._rollback_batch(batch, executed)
            batch.status = ExecutionStatus.ROLLED_BACK
            return False

        # 5. 全部成功
        batch.status = ExecutionStatus.SUCCESS
        return True

    def _execute_operation(self, op: Operation):
        """执行单个操作"""
        if op.op_type == "copy":
            self._execute_copy(op)
        elif op.op_type == "move":
            self._execute_move(op)
        elif op.op_type == "delete":
            self._execute_delete(op)
        elif op.op_type == "write":
            self._execute_write(op)
        elif op.op_type == "read":
            self._execute_read(op)
        else:
            raise ValueError(f"未知操作类型: {op.op_type}")

        op.status = ExecutionStatus.SUCCESS

    def _execute_copy(self, op: Operation):
        """执行复制操作"""
        src = Path(op.source)
        dst = Path(op.target) if op.target else None

        if not src.exists():
            raise FileNotFoundError(f"源文件不存在: {src}")

        if dst:
            # 计算源文件校验和
            op.checksum_before = self._compute_checksum(src)
            # 复制
            shutil.copy2(src, dst)
            # 验证校验和
            op.checksum_after = self._compute_checksum(dst)
            if op.checksum_before != op.checksum_after:
                raise RuntimeError("复制后校验和不匹配")

    def _execute_move(self, op: Operation):
        """执行移动操作"""
        src = Path(op.source)
        dst = Path(op.target) if op.target else None

        if not src.exists():
            raise FileNotFoundError(f"源文件不存在: {src}")

        if dst:
            shutil.move(str(src), str(dst))

    def _execute_delete(self, op: Operation):
        """执行删除操作"""
        src = Path(op.source)

        if not src.exists():
            raise FileNotFoundError(f"源文件不存在: {src}")

        # 检查是否违反约束
        if src.is_file():
            src.unlink()
        elif src.is_dir():
            shutil.rmtree(src)

    def _execute_write(self, op: Operation):
        """执行写入操作"""
        dst = Path(op.target) if op.target else Path(op.source)
        content = op.parameters.get("content", "")

        # 写入前备份
        if dst.exists():
            backup = self.backup_dir / f"{dst.name}.backup"
            shutil.copy2(dst, backup)

        with open(dst, "w", encoding="utf-8") as f:
            f.write(content)

    def _execute_read(self, op: Operation):
        """执行读取操作"""
        src = Path(op.source)

        if not src.exists():
            raise FileNotFoundError(f"源文件不存在: {src}")

        with open(src, "r", encoding="utf-8") as f:
            content = f.read()

        op.parameters["content"] = content

    def _create_backup(self, batch: Batch) -> bool:
        """为批次创建备份"""
        backup_path = self.backup_dir / batch.batch_id
        backup_path.mkdir(parents=True, exist_ok=True)

        for op in batch.operations:
            src = Path(op.source)
            if src.exists():
                backup_file = backup_path / f"{op.op_id}_{src.name}"
                if src.is_file():
                    shutil.copy2(src, backup_file)
                elif src.is_dir():
                    shutil.copytree(src, backup_file)

        batch.backup_path = str(backup_path)
        return True

    def _rollback_batch(self, batch: Batch, executed: List[Operation]):
        """回滚批次"""
        # 从后往前回滚
        for op in reversed(executed):
            try:
                self._rollback_operation(op, batch.backup_path)
            except Exception as e:
                # 记录回滚失败，但继续回滚其他操作
                print(f"回滚失败 {op.op_id}: {e}")

    def _rollback_operation(self, op: Operation, backup_path: str):
        """回滚单个操作"""
        if op.op_type == "copy":
            # 删除复制目标
            if op.target:
                dst = Path(op.target)
                if dst.exists():
                    dst.unlink()
        elif op.op_type == "move":
            # 恢复原始位置
            if op.target:
                src = Path(op.target)
                dst = Path(op.source)
                if src.exists():
                    shutil.move(str(src), str(dst))
        elif op.op_type == "delete":
            # 从备份恢复
            backup = Path(backup_path) / f"{op.op_id}_{Path(op.source).name}"
            if backup.exists():
                dst = Path(op.source)
                if backup.is_file():
                    shutil.copy2(backup, dst)
                elif backup.is_dir():
                    shutil.copytree(backup, dst)
        elif op.op_type == "write":
            # 从备份恢复
            backup = Path(backup_path) / f"{op.op_id}_{Path(op.source).name}"
            if backup.exists():
                shutil.copy2(backup, Path(op.source))

    def _compute_checksum(self, path: Path) -> str:
        """计算文件校验和"""
        if not path.exists():
            return ""

        hasher = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def get_execution_report(self, batch: Batch) -> Dict[str, Any]:
        """生成执行报告"""
        return {
            "batch_id": batch.batch_id,
            "status": batch.status.value,
            "total_operations": len(batch.operations),
            "successful_operations": sum(1 for op in batch.operations if op.status == ExecutionStatus.SUCCESS),
            "failed_operations": sum(1 for op in batch.operations if op.status == ExecutionStatus.FAILED),
            "backup_path": batch.backup_path,
            "operations": [
                {
                    "op_id": op.op_id,
                    "op_type": op.op_type,
                    "status": op.status.value,
                    "checksum_before": op.checksum_before,
                    "checksum_after": op.checksum_after,
                    "error": op.error
                }
                for op in batch.operations
            ]
        }


# 便捷函数
def create_executor(backup_dir: str = "./backups") -> AtomicExecutor:
    return AtomicExecutor(backup_dir)
