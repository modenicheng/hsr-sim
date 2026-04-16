# HSR-Sim Event 系统用法说明

**版本**：1.0
**更新日期**：2026-04-15

本文档详细说明项目中基于 `eventure` 的事件系统如何使用，包括：事件定义、订阅与发布、优先级、事件日志、回放、与 Hook 协作以及确定性建议。

---

## 1. 设计定位

在当前实现中：

- **Event 系统**用于通知“已经发生了什么”。
- **Hook 系统**用于干预“正在计算什么”。

建议遵循以下分工：

- Hook：可改值、可中断流程（例如伤害结算前的增减伤计算）。
- Event：只广播结果，不反向修改主流程（例如最终伤害已落地）。

> 一句话：**先 Hook 计算最终结果，再 Event 广播结果事实**。

---

## 2. 代码入口总览

### 2.1 全局事件入口（兼容层）

文件：`src/hsr_sim/events/__init__.py`

导出对象：

- `EventType`：事件类型枚举
- `GameEvent`：项目级事件模型（Pydantic）
- `GameEventBus`：项目封装总线
- `event_log`：全局 `EventLog`
- `bus`：原生 `eventure.EventBus`
- `game_bus`：封装后的 `GameEventBus`

### 2.2 战斗世界入口（推荐）

文件：`src/hsr_sim/ecs/world.py`

每个 `ECSWorld` 实例都会创建独立的：

- `self.event_log: EventLog`
- `self.event_bus: EventBus`
- `self.event_stream: GameEventBus`

并提供快捷发布：

- `publish_event(event: GameEvent)`

> 推荐在战斗流程中使用 `world.event_stream`（或 `world.publish_event`），而不是跨战斗共用全局总线。

---

## 3. 事件类型与数据模型

### 3.1 `EventType` 枚举

文件：`src/hsr_sim/events/types.py`

当前内置事件类型：

- `DAMAGE_DEALT`
- `SKILL_EXECUTED`
- `TURN_STARTED`
- `TURN_ENDED`
- `BUFF_APPLIED`
- `BUFF_EXPIRED`
- `HEALING_DONE`
- `ENERGY_CHANGED`

新增类型时建议：

1. 先在 `EventType` 中加枚举值。
2. 再由业务模块统一发布，避免手写字符串。

### 3.2 `GameEvent` 模型

文件：`src/hsr_sim/events/models.py`

字段说明：

- `tick: int`（必填，`>= 0`）
- `type: EventType`（必填）
- `data: dict[str, Any]`（事件载荷）
- `timestamp: float | None`（可选，默认自动生成）
- `event_id: str | None`（可选）
- `parent_id: str | None`（可选，事件因果链）

关键能力：

- `to_eventure_event()`：转换为 `eventure.Event`
- `from_eventure_event()`：从 `eventure.Event` 恢复

建议规范：

- `data` 仅放可序列化字段（数字、字符串、布尔、列表、字典）。
- 不要把 ORM 对象、函数、上下文对象直接塞入 `data`。

---

## 4. 订阅事件

### 4.1 基础订阅

`GameEventBus.subscribe()` 签名：

- `event_type: EventType | str`
- `handler: Callable[[Event], None]`
- `priority: int = 0`
- `owner: str | None = None`

返回 `SubscriptionHandle`，可用于后续取消订阅。

示例：

```python
from hsr_sim.events import EventType


def on_damage(event):
    amount = event.data.get("amount", 0)
    print("damage dealt:", amount)

handle = world.event_stream.subscribe(
    EventType.DAMAGE_DEALT,
    on_damage,
    priority=100,
    owner="damage_stats",
)
```

### 4.2 优先级规则

同一 `event_type` 下回调执行顺序为：

1. `priority` 高者先执行
2. `priority` 相同按注册顺序执行

### 4.3 取消订阅

- 按句柄取消：`unsubscribe(handle)`
- 按 owner 批量取消：`unsubscribe_owner("damage_stats")`

示例：

```python
world.event_stream.unsubscribe(handle)
# 或
world.event_stream.unsubscribe_owner("damage_stats")
```

---

## 5. 发布事件

### 5.1 通用发布

可以先构建 `GameEvent` 再发布：

```python
from hsr_sim.events import EventType, GameEvent

world.publish_event(
    GameEvent(
        tick=10,
        type=EventType.TURN_STARTED,
        data={"actor_id": 1001},
    )
)
```

也可以直接调用：

```python
world.event_stream.publish(
    GameEvent(
        tick=10,
        type=EventType.TURN_STARTED,
        data={"actor_id": 1001},
    )
)
```

### 5.2 便捷发布方法

当前封装提供：

- `publish_damage_event(...)`
- `publish_skill_executed_event(...)`

示例：

```python
world.event_stream.publish_damage_event(
    tick=12,
    amount=888,
    source_id=1001,
    target_id=2001,
    critical=True,
    damage_type="quantum",
)

world.event_stream.publish_skill_executed_event(
    tick=12,
    skill_name="resurgence",
    source_id=1001,
    target_id=2001,
)
```

---

## 6. Tick 语义与约束

`GameEventBus` 会保证事件 tick 单调不回退：

- 若新事件 `tick < event_log.current_tick`：抛出 `ValueError`
- 若新事件 `tick > current_tick`：自动推进 `EventLog` 到该 tick

因此建议在战斗主循环中维护一个统一 tick 源，所有发布都使用同一来源。

---

## 7. 事件日志与持久化

### 7.1 自动记录

事件通过 `publish()` / `dispatch()` 发出后，会被追加到对应 `EventLog`。

读取日志：

```python
events = world.event_stream.event_log.events
```

### 7.2 保存与加载（eventure 原生）

```python
# 保存到文件
world.event_stream.event_log.save_to_file("battle_events.log")

# 从文件加载为新的 EventLog
from eventure import EventLog
loaded_log = EventLog.load_from_file("battle_events.log")
```

如果要落库，可将事件序列转换为 JSON 结构写入 `BattleRecord.record_data`。

建议最小结构：

- `config_version`
- `seed`
- `events`（按顺序）
- `result_summary`

---

## 8. 回放（Replay）

`GameEventBus` 提供：

- `replay(events: Iterable[GameEvent | Event])`

示例：

```python
new_world = ECSWorld(config_version="v1.0")
new_world.event_stream.replay(loaded_log.events)
```

回放注意点：

1. 推荐使用“新的”战斗世界和总线，避免污染正在运行的日志。
2. 回放输入必须保持原始顺序。
3. 若需要严格复现，还需复原同一随机种子和初始状态。

---

## 9. 与 Hook 协作模式（推荐模板）

典型伤害流程建议：

1. 触发 `HookRegistry` 干预，得到最终伤害值。
2. 应用伤害到实体状态。
3. 发布 `DAMAGE_DEALT` 事件通知外部模块（统计、追击判定、UI 展示等）。

示例伪代码：

```python
# 1) Hook 干预计算
result = world.hook_registry.trigger(
    HookPoint.BEFORE_DAMAGE_CALCULATION,
    base_damage,
    attacker_id=attacker,
    defender_id=defender,
)
final_damage = int(result.value)

# 2) 应用结果
apply_damage(defender, final_damage)

# 3) 发布事件（通知）
world.event_stream.publish_damage_event(
    tick=current_tick,
    amount=final_damage,
    source_id=attacker,
    target_id=defender,
)
```

---

## 10. 最佳实践

1. **事件负载最小化**：`data` 存 ID 和必要快照，不存大对象。
2. **统一命名**：所有事件名走 `EventType`，不要散落硬编码字符串。
3. **按 owner 管理订阅**：系统销毁时可批量注销。
4. **避免事件循环**：事件处理器中谨慎再次发布同类事件，防止递归风暴。
5. **一战斗一总线**：每个 `ECSWorld` 使用独立事件流更易隔离与回放。
6. **可测试**：新增事件时同步补测试（订阅顺序、日志写入、回放结果）。

---

## 11. 常见问题（FAQ）

### Q1：什么时候用全局 `game_bus`，什么时候用 `world.event_stream`？

- 战斗流程：优先用 `world.event_stream`（隔离性好）。
- 跨战斗工具或临时脚本：可使用全局 `game_bus`。

### Q2：可以直接用原生 `EventBus.publish()` 吗？

可以，但不推荐在业务代码中直接依赖原生接口。推荐统一通过 `GameEventBus`，便于后续扩展。

### Q3：为什么不把 Hook 和 Event 合并？

职责不同：Hook 负责“改流程”，Event 负责“广播事实”。合并会让可维护性和调试复杂度显著上升。

---

## 12. 后续扩展建议

1. 增加更多便捷发布方法（如 `publish_turn_started_event`）。
2. 增加事件 schema 版本号字段，提升历史兼容性。
3. 增加事件回放校验工具（比较回放前后关键状态哈希）。
4. 将战斗事件序列标准化后接入 `BattleRecord.record_data`。

---

如本文档与代码不一致，请以 `src/hsr_sim/events/` 与 `src/hsr_sim/ecs/world.py` 的当前实现为准，并及时更新文档。
