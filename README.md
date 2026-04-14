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

### Examples

```sh
uv run .\scripts\create_character.py seele -f
uv run .\scripts\create_relic_set.py rutilant_arena -t planar_ornaments
uv run .\scripts\create_light_cone.py in_the_night -v v1.0

# batch mode
uv run .\scripts\create_character.py seele sunday -f
uv run .\scripts\create_relic_set.py genius_of_brilliant_stars rutilant_arena -t relics
uv run .\scripts\create_light_cone.py in_the_night a_grounded_ascent -v v1.0
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

说明：

- 脚手架脚本默认会在对应号段内自动分配顺序 ID（按当前 `configs/<version>` 已存在配置递增）。
- `--force` 仅覆盖同名目录，不会重置全局递增计数；新生成 ID 仍遵循“同号段取当前最大值 + 1”。

## Design Docs

在 `docs` 目录下的 `design.md` 。系统架构设计在这里。在动代码前最好先看看这个文档
