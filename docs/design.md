# 系统框架设计

## 主要构成

- 事件系统 / 事件总线
  - `Eventure`
- ECS 系统
  - Entity Component System，实体负责标记，组件负责数据，系统负责计算
  - `Esper`
- 状态机，管理角色状态（每个角色实例一个，不共享）
  - `Transitions`
- 数据层
  - Pydantic 数据校验与接口数据格式封装
  - SQLAlchemy 数据持久化
  - Alembic 数据库迁移
  - psql / sqlite 数据库后端

- 预留 AI 接入接口
