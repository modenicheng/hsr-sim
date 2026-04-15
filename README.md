# HSR Simulator

## Install deps

使用 `uv` 作为管理器

```sh
uv sync
```

## Code quality (prek)

项目使用 `prek` 管理 Git hooks（见根目录 `prek.toml`）：

- `ruff-check --fix` + `ruff-format`：统一 Python 代码风格与格式
- `conventional-pre-commit`：在 `commit-msg` 阶段校验 Conventional Commit
- 内置基础检查：如尾随空格、文件结尾换行、私钥检测等

首次启用（Windows 可用 `uv tool install prek` 或 `winget install --id j178.Prek` 安装）：

```sh
prek install -f --prepare-hooks
```

手动全量执行：

```sh
prek run --all-files
```

## Run the project

项目使用了 src 布局，所以需要使用模块的方式启动：

```sh
uv run -m hsr_sim
```

## Scaffolding scripts

项目提供了几个配置脚手架脚本，用于快速生成角色、遗器套装和光锥的配置文件骨架。

### Create a character

```sh
uv run .\scripts\create_character.py <character_name...> [--version v1.0] [-f]
```

- `character_name...`：必填，可输入一个或多个角色名，仅允许英文字符和 `_`
- `--version`：可选，版本号，支持 `x.x` 或 `vx.x`，默认 `v1.0`
- `-f / --force`：可选，强制覆写已存在的同名角色目录

输出目录：

```text
configs/<version>/characters/<character_name>/
```

角色主 JSON（`<character_name>.json`）中的关键结构：

- 技能相关：`basic_atk` / `skill` / `ultimate`（均为嵌套对象）
- 星魂：`eidolons`（嵌套对象列表）
- 天赋：`talents`（嵌套对象列表）
- 秘技：`technique`（嵌套对象）
- 额外能力：`bonus_abilities`（嵌套对象列表）
- 能量配置：`energy`（嵌套对象，包含 `energy_type` 与 `max_energy`）

说明：`talent_ids / technique_id / bonus_ability_ids` 已改为上述嵌套结构。

### Create a relic set

```sh
uv run .\scripts\create_relic_set.py <name...> -t <relics|planar_ornaments> [--version v1.0] [-f]
```

- `name...`：必填，可输入一个或多个套装名称，仅允许英文字符和 `_`
- `-t / --type`：必填，套装类型
  - `relics`：外圈遗器，创建 `head / hands / torso / feet`
  - `planar_ornaments`：位面饰品，创建 `planar_sphere / link_rope`
- `--version`：可选，版本号，支持 `x.x` 或 `vx.x`，默认 `v1.0`
- `-f / --force`：可选，强制覆写已存在的同名套装目录

输出目录：

```text
configs/<version>/relics/<name>/
```

### Create a light cone

```sh
uv run .\scripts\create_light_cone.py <name...> [--version v1.0] [-f]
```

- `name...`：必填，可输入一个或多个光锥名称，仅允许英文字符和 `_`
- `--version / -v`：可选，版本号，支持 `x.x` 或 `vx.x`，默认 `v1.0`
- `-f / --force`：可选，强制覆写已存在的同名光锥目录

输出目录：

```text
configs/<version>/light_cones/<name>/
```

### Create a buff

```sh
uv run .\scripts\create_buff.py <buff_name> [--version v1.0] [-f]
uv run .\scripts\create_buff.py overload <character_name> <buff_name> [--version v1.0] [-f]
```

- `buff_name`：必填，仅允许英文字符和 `_`
- `overload`：可选模式标记；出现时表示创建**角色专属 Buff**
- `character_name`：`overload` 模式下必填，角色名仅允许英文字符和 `_`
- `--version / -v`：可选，版本号，支持 `x.x` 或 `vx.x`，默认 `v1.0`
- `-f / --force`：可选，强制覆写已存在的同名 Buff 目录

输出目录：

```text
configs/<version>/buffs/<buff_name>/
configs/<version>/characters/<character_name>/buffs/<buff_name>/
```

#### Buff 配置约定

项目中的 Buff 配置采用“**全局目录 + 角色可覆写**”的混合方案：

- **全局 Buff**：放在 `configs/<version>/buffs/` 下，适合通用增益、减益、召唤物效果等可复用配置。
- **角色专属 Buff**：放在 `configs/<version>/characters/<character_name>/buffs/` 下，用于只服务于单个角色机制的特殊效果。
- **加载优先级**：当同名或同 ID 的 Buff 同时存在时，角色专属配置优先于全局配置。
### Create an enemy

```sh
uv run .\scripts\create_enemy.py <enemy_name...> [--version v1.0] [-f]
```

- `enemy_name...`：必填，可输入一个或多个敌人名，仅允许英文字符和 `_`
- `--version`：可选，版本号，支持 `x.x` 或 `vx.x`，默认 `v1.0`
- `-f / --force`：可选，强制覆写已存在的同名敌人目录

输出目录：

```text
configs/<version>/enemies/<enemy_name>/
```

敌人配置包含：

- 主 JSON：`<enemy_name>.json`，包含 ID、名称、属性、弱点、韧性、技能与被动。
- 技能脚本：`skills/<enemy_name>_skill.py`
- 被动脚本：`passives/<enemy_name>_passive.py`

### Migrate character configs

```sh
uv run .\scripts\migrate_character_configs.py [--version v1.0] [--write]
```

- `--version`：可选，目标版本，支持 `x.x` 或 `vx.x`。默认迁移所有版本。
- `--write`：可选，写回更改到文件。不传此参数则为 **dry-run** 模式，仅显示统计。

功能：

- 扫描指定版本（或所有版本）的角色配置文件。
- 补齐新增的 schema 字段（如 `energy` 等）。
- **不覆盖**已存在的值，仅填补缺失字段。
- 迁移后的配置必须通过 Pydantic schema 校验。

### Validate configs

```sh
uv run .\scripts\validate_configs.py [--version v1.0]
```

- `--version`：可选，校验特定版本，支持 `x.x` 或 `vx.x`。默认校验所有版本。

功能：

- **ID 唯一性检查**：扫描所有配置文件，检测全局 ID 重复。
- **JSON 格式校验**：验证 JSON 文件的格式有效性。
- **Python 脚本规范检查**：
  - 语法错误检测
  - 验证导入 `BaseSkill` 类
  - 验证类定义存在
  - 检查 `execute` 方法

输出：使用 `rich` 生成美观的终端报告，包含错误表、警告表和汇总统计。

### Examples

使用完整命令：

```sh
uv run .\scripts\create_character.py seele -f
uv run .\scripts\create_relic_set.py rutilant_arena -t planar_ornaments
uv run .\scripts\create_light_cone.py in_the_night -v v1.0
uv run .\scripts\create_buff.py team_buff
uv run .\scripts\create_enemy.py mara_struck_soldier
uv run .\scripts\migrate_character_configs.py --write
uv run .\scripts\validate_configs.py

# 批量模式
uv run .\scripts\create_character.py seele sunday -f
uv run .\scripts\create_relic_set.py genius_of_brilliant_stars rutilant_arena -t relics
uv run .\scripts\create_light_cone.py in_the_night a_grounded_ascent -v v1.0
uv run .\scripts\create_enemy.py mara_struck_soldier weakling -f
```

## ID 约定

- `10xxxxxx`：角色主配置（Character，2+6 位）
  - `11xxxxxx`：角色普攻（Basic ATK）
  - `12xxxxxx`：角色战技（Skill）
  - `13xxxxxx`：角色终结技（Ultimate）
  - `14xxxxxx`：角色星魂（Eidolon）
  - `15xxxxxx`：角色天赋（Talent）
  - `16xxxxxx`：角色秘技（Technique）
  - `17xxxxxx`：角色额外能力（Bonus Ability）

- `20xxxxxx`：遗器套装（Relic Set，2+6 位）
  - `21xxxxxx`：遗器单件（按部位，如 `head` / `link_rope`）
  - `22xxxxxx`：2 件套效果（Passive 2pc）
  - `23xxxxxx`：4 件套效果（Passive 4pc）

- `30xxxxxx`：光锥主配置（Light Cone，2+6 位）
  - `31xxxxxx`：光锥被动（Passive Skill）

- `40xxxxxx`：敌人主配置（Enemy，2+6 位）
  - `41xxxxxx`：敌人技能（Enemy Skill）
  - `42xxxxxx`：敌人被动（Enemy Passive）

- `50xxxxxx`：全局增益/减益（Global Buff，2+6 位）
- `51xxxxxx`：角色专属增益/减益（Character Buff，2+6 位）

说明：

- 脚手架脚本默认会在对应号段内自动分配顺序 ID（按当前 `configs/<version>` 已存在配置递增）。
- `--force` 仅覆盖同名目录，不会重置全局递增计数；新生成 ID 仍遵循“同号段取当前最大值 + 1”。

## Design Docs

在 `docs` 目录下的 `design.md` 。系统架构设计在这里。在动代码前最好先看看这个文档
