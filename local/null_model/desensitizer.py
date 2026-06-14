"""
Desensitizer - 脱敏处理

根据隐私资料库的调度指令，对事实进行脱敏。
"""

from typing import List, Dict, Any


class Desensitizer:
    """脱敏处理器"""

    def process(self, ranked_facts: List[Dict], schedule) -> List[Dict]:
        """对高相关事实进行脱敏"""
        desensitized = []

        for r in ranked_facts:
            if r["relevance"] < 0.3:
                continue

            fact = r["fact"]
            value = fact.value

            # 时间粒度脱敏
            if fact.attribute == "timestamp" and isinstance(value, str):
                if "T" in value:
                    value = value[:13] + ":00:00"

            # 区域匿名化
            if "location" in fact.entity or "zone" in fact.attribute:
                value = self._alias_zone(str(value))

            desensitized.append({
                "fact_id": fact.fact_id,
                "entity": fact.entity,
                "attribute": fact.attribute,
                "value": value,
                "relevance": r["relevance"]
            })

        return desensitized

    def _alias_zone(self, zone_id: str) -> str:
        alias_map = {"living_room": "Zone-A", "bedroom": "Zone-B", "kitchen": "Zone-C"}
        return alias_map.get(zone_id, "Zone-X")
