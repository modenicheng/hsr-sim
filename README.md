# HSR Simulator

## Install deps

使用 `uv` 作为管理器

```sh
uv sync
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
uv run .\scripts\create_character.py <character_name> [--version v1.0] [-f]
```

- `character_name`：必填，角色名，仅允许英文字符和 `_`
- `--version`：可选，版本号，支持 `x.x` 或 `vx.x`，默认 `v1.0`
- `-f / --force`：可选，强制覆写已存在的同名角色目录

输出目录：

```text
configs/<version>/characters/<character_name>/
```

### Create a relic set

```sh
uv run .\scripts\create_relic_set.py <name> -t <relics|planar_ornaments> [--version v1.0] [-f]
```

- `name`：必填，套装名称，仅允许英文字符和 `_`
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
uv run .\scripts\create_light_cone.py <name> [--version v1.0] [-f]
```

- `name`：必填，光锥名称，仅允许英文字符和 `_`
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
```
