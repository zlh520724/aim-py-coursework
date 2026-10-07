# -*- coding: utf-8 -*-
"""AIM 2627 Python Coursework —— 哨兵 Sentry 控制模块（学生骨架）。

你的全部作业都在本文件里：按题面（题面.pdf）各题的规范补全每个标有 TODO 的函数。
- 骨架已提供：Facing / SentryState 枚举、SentryGrid 的构造与只读属性、
  渲染函数 render_frame（demo 用，不进测试）。
- 你要实现：Q1-Q6 与 Bonus 的全部 TODO，以及 SentryGrid 的
  四个方法（current_pos 的 setter、move_forward、turn_left、turn_right）。
- 未实现的函数 raise NotImplementedError：可见测试会自动 skip，
  CI 一开始就是绿的；实现一个，对应测试亮一个。
- `python main.py`（或 PYTHONPATH=src python -m main）可看 ASCII 演示。
"""
import json
from enum import Enum


# ---------------------------------------------------------------------------
# 仿真世界基础（已提供，勿改）
# ---------------------------------------------------------------------------
class Facing(Enum):
    """朝向枚举。世界坐标 (x, y)：x 向右增长，y 向上增长（数学系）。"""

    UP = (0, 1)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def delta(self):
        """该朝向的单位位移向量 (dx, dy)。"""
        return self.value[0], self.value[1]


# ---------------------------------------------------------------------------
# Q1 机器人自检（题面 Q1·自检状态计算与报告生成）
# ---------------------------------------------------------------------------
def hp_ratio(hp, max_hp):
    if max_hp <= 0:
        return 0
    if isinstance(hp, int) and isinstance(max_hp, int):
        return max(0, min(100, hp * 100 // max_hp))
    return max(0, min(100, int(hp * 100 / max_hp)))


def status_report(name, robot_type, hp, max_hp, battery):
    if battery < 20:
        level = "LOW"
    elif battery < 60:
        level = "WARNING"
    else:
        level = "OK"

    ratio = hp_ratio(hp, max_hp)
    return (
        f"{name:<10}|{robot_type:^10}|"
        f"HP {ratio:>3}%|BAT {battery:>3}%|{level}"
    )


# ---------------------------------------------------------------------------
# Q2 战斗日志分析（题面 Q2·多源日志解析与统计）
def analyze_damage_log(lines):
    import json
    import re

    by_armor = {"front": 0, "left": 0, "right": 0}
    armor_map = {"F": "front", "L": "left", "R": "right"}
    seen_ids = set()
    unhashable_ids = []
    sensor_pattern = re.compile(r"([FLR]):\s*([0-9]+)")
    event_count = 0

    for line in lines:
        if not isinstance(line, str):
            continue

        text = line.strip()
        if not text or text.startswith("#"):
            continue

        events = []

        if text.startswith("{"):
            try:
                record = json.loads(text)
            except (ValueError, RecursionError):
                continue

            if not isinstance(record, dict):
                continue

            armor = record.get("armor")
            damage = record.get("damage")

            if not isinstance(armor, str) or armor not in by_armor:
                continue

            # Reject booleans, floats, strings, and nonpositive integers.
            if type(damage) is not int or damage <= 0:
                continue

            if "id" in record:
                record_id = record["id"]
                try:
                    if record_id in seen_ids:
                        continue
                    seen_ids.add(record_id)
                except TypeError:
                    if record_id in unhashable_ids:
                        continue
                    unhashable_ids.append(record_id)

            events.append((armor, damage))
        else:
            valid = True

            for segment in text.split(","):
                match = sensor_pattern.fullmatch(segment.strip())
                if match is None:
                    valid = False
                    break

                try:
                    damage = int(match.group(2))
                except ValueError:
                    valid = False
                    break

                if damage <= 0:
                    valid = False
                    break

                armor = armor_map[match.group(1)]
                events.append((armor, damage))

            # Discard the entire line if any segment is invalid.
            if not valid:
                continue

        for armor, damage in events:
            by_armor[armor] += damage
            event_count += 1

    total = sum(by_armor.values())
    most_hit = (
        max(by_armor, key=by_armor.get) if event_count else None
    )
    avg = round(total / event_count, 2) if event_count else 0.0

    return {
        "total": total,
        "by_armor": by_armor,
        "most_hit": most_hit,
        "avg": avg,
    }

# ---------------------------------------------------------------------------
# Q3 SentryGrid（题面 Q3·载体物理规则）
# ---------------------------------------------------------------------------


class SentryGrid:
    """哨兵仿真载体（构造与只读属性已提供；四个 TODO 方法由你实现）。"""

    def __init__(self, width, height, obstacles, enemy_pos,
                 start_pos=(0, 0), facing=Facing.UP, fuel=100):
        self._width = int(width)
        self._height = int(height)
        if self._width <= 0 or self._height <= 0:
            raise ValueError("地图尺寸必须为正")
        # 障碍坐标存入 set，查询 O(1)——已有实现，勿改。
        self._obstacles = set()
        for ob in obstacles:
            x, y = ob
            self._obstacles.add((int(x), int(y)))
        if not isinstance(enemy_pos, (tuple, list)) or len(enemy_pos) != 2:
            raise TypeError("enemy_pos 需要长度为 2 的 tuple/list")
        self._enemy_pos = self._clamp_cell(enemy_pos)
        if self._enemy_pos in self._obstacles:
            raise ValueError("enemy_pos 不能位于障碍物上")
        if not isinstance(facing, Facing):
            facing = Facing.UP
        self._facing = facing
        self._fuel = int(fuel)
        self._collision_count = 0
        self.current_pos = start_pos
        if self._pos in self._obstacles:
            raise ValueError("start_pos 不能位于障碍物上")

    def _clamp_cell(self, cell):
        """已提供：元素转 int 并夹回地图范围（供 __init__ 使用）。"""
        x = int(cell[0])
        y = int(cell[1])
        x = max(0, min(self._width - 1, x))
        y = max(0, min(self._height - 1, y))
        return (x, y)

    # -- 只读属性（已提供，勿改） ------------------------------------------
    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def enemy_pos(self):
        return self._enemy_pos

    @property
    def facing(self):
        return self._facing

    @property
    def fuel(self):
        return self._fuel

    @property
    def collision_count(self):
        return self._collision_count

    @property
    def obstacles(self):
        """障碍集合的只读视图（内部 set 引用，不要修改它）。"""
        return self._obstacles

    @property
    def found_enemy(self):
        return self._pos == self._enemy_pos

    def is_blocked(self, x, y):
        """已提供：坐标是否为障碍或越界（O(1)）。"""
        return ((x, y) in self._obstacles
                or not (0 <= x < self._width and 0 <= y < self._height))

    # -- 你要实现的部分 ------------------------------------------------------
    @property
    def current_pos(self):
        """当前位置 (x, y) 的 tuple。"""
        return self._pos

    @current_pos.setter
    def current_pos(self, value):
        if not isinstance(value, (tuple, list)) or len(value) != 2:
            raise TypeError("current_pos must be a tuple or list of length 2")

        self._pos = self._clamp_cell(value)

    def move_forward(self):
        if self._fuel <= 0:
            return self._pos

        self._fuel -= 1

        x, y = self._pos
        dx, dy = self._facing.delta
        next_x, next_y = x + dx, y + dy

        if self.is_blocked(next_x, next_y):
            self._collision_count += 1
        else:
            self._pos = (next_x, next_y)

        return self._pos

    def turn_left(self):
        left_turn = {
            Facing.UP: Facing.LEFT,
            Facing.LEFT: Facing.DOWN,
            Facing.DOWN: Facing.RIGHT,
            Facing.RIGHT: Facing.UP,
        }
        self._facing = left_turn[self._facing]
        return self._facing

    def turn_right(self):
        right_turn = {
            Facing.UP: Facing.RIGHT,
            Facing.RIGHT: Facing.DOWN,
            Facing.DOWN: Facing.LEFT,
            Facing.LEFT: Facing.UP,
        }
        self._facing = right_turn[self._facing]
        return self._facing


# ---------------------------------------------------------------------------
# Q4 贪心导航（题面 Q4·单步贪心导航策略）
# ---------------------------------------------------------------------------
def next_step_toward(pos, target, obstacles, current_facing=Facing.UP):
    x, y = pos
    target_x, target_y = target
    dx = target_x - x
    dy = target_y - y

    horizontal = Facing.RIGHT if dx > 0 else Facing.LEFT
    vertical = Facing.UP if dy > 0 else Facing.DOWN
    candidates = []
    if dx:
        candidates.append((abs(dx), horizontal))
    if dy:
        candidates.append((abs(dy), vertical))

    # Stable sorting preserves horizontal priority when differences tie.
    candidates.sort(key=lambda item: item[0], reverse=True)
    for _, direction in candidates:
        step_x, step_y = direction.delta
        if (x + step_x, y + step_y) not in obstacles:
            return direction
    return current_facing


# ---------------------------------------------------------------------------
# Q5 哨兵决策机（题面 Q5·裁判系统决策规则表）
# ---------------------------------------------------------------------------
class SentryState(Enum):
    """哨兵状态机（已提供，勿改）。"""

    PATROL = "PATROL"
    SUSPECT = "SUSPECT"
    ENGAGE = "ENGAGE"
    RETREAT = "RETREAT"
    RETURN = "RETURN"


def decide(sensor, state, hp, heat):
    required = ("enemy_frames", "enemy_dist", "robot_type", "max_hp")

    if not isinstance(sensor, dict):
        raise ValueError("sensor must be a dictionary")

    if any(key not in sensor for key in required):
        raise ValueError("sensor is missing required fields")

    if not isinstance(state, SentryState):
        raise ValueError("state must be a SentryState member")

    frames = sensor["enemy_frames"]
    if not isinstance(frames, (tuple, list)):
        raise ValueError("enemy_frames must be a tuple or list")

    if not 1 <= len(frames) <= 6:
        raise ValueError("enemy_frames length must be between 1 and 6")

    frames = tuple(bool(frame) for frame in frames)

    enemy_dist = sensor["enemy_dist"]
    if type(enemy_dist) is not int or enemy_dist < 0:
        enemy_dist = float("inf")

    robot_type = sensor["robot_type"]
    if robot_type not in ("INFANTRY", "HERO"):
        robot_type = "INFANTRY"

    try:
        max_hp = int(sensor["max_hp"])
    except (TypeError, ValueError, OverflowError):
        max_hp = 100

    if max_hp <= 0:
        max_hp = 100

    try:
        normalized_hp = int(hp)
    except (TypeError, ValueError, OverflowError):
        normalized_hp = 0

    hp_pct = hp_ratio(normalized_hp, max_hp)
    visible = frames[-1]

    def engage_action():
        if enemy_dist <= 3:
            return ("SHOOT", SentryState.ENGAGE)
        action = "MOVE_RIGHT" if robot_type == "HERO" else "MOVE_LEFT"
        return (action, SentryState.ENGAGE)

    # R1: Low health overrides every other rule.
    if hp_pct <= 30:
        return ("RETREAT", SentryState.RETREAT)

    # R2: Remain in retreat until health reaches the assumed threshold.
    if state == SentryState.RETREAT:
        if hp_pct >= 60:
            return ("RETURN", SentryState.RETURN)
        return ("RETREAT", SentryState.RETREAT)

    # R3: RETURN is a one-frame transition.
    if state == SentryState.RETURN:
        return ("MOVE_BASE", SentryState.PATROL)

    # R4: Engage a currently visible enemy.
    if state == SentryState.ENGAGE and visible:
        return engage_action()

    # R5: Two trailing false frames mean sustained loss.
    if state == SentryState.ENGAGE:
        sustained_loss = len(frames) >= 2 and not any(frames[-2:])
        if sustained_loss:
            return ("SCAN", SentryState.SUSPECT)
        return ("HOLD_FIRE", SentryState.ENGAGE)

    # R6: Confirm an enemy using two consecutive visible frames.
    if visible:
        confirmed = len(frames) >= 2 and frames[-2]
        if not confirmed:
            return ("SCAN", SentryState.SUSPECT)

        return engage_action()

    # R7: Default behavior without a visible enemy.
    if state == SentryState.PATROL:
        return ("PATROL_MOVE", SentryState.PATROL)

    return ("SCAN", SentryState.SUSPECT)


# ---------------------------------------------------------------------------
# Q6 巡逻任务（题面 Q6·巡逻契约与验收阈值）
# ---------------------------------------------------------------------------
def run_patrol(grid, max_steps=500):
    from collections import deque

    directions = (
        Facing.UP,
        Facing.RIGHT,
        Facing.DOWN,
        Facing.LEFT,
    )

    def distance(pos, target):
        return abs(pos[0] - target[0]) + abs(pos[1] - target[1])

    def escape_path(start, target):
        queue = deque([start])
        previous = {start: None}

        while queue:
            pos = queue.popleft()

            if pos == target:
                path = []
                while previous[pos] is not None:
                    parent, direction = previous[pos]
                    path.append(direction)
                    pos = parent
                path.reverse()
                return deque(path)

            for direction in directions:
                dx, dy = direction.delta
                next_pos = (pos[0] + dx, pos[1] + dy)

                if next_pos in previous:
                    continue
                if grid.is_blocked(*next_pos):
                    continue

                previous[next_pos] = (pos, direction)
                queue.append(next_pos)

        return deque()

    steps = 0
    initial_collisions = grid.collision_count
    visited = {grid.current_pos}
    planned_path = deque()
    unreachable = False

    while (
        steps < max_steps
        and grid.fuel > 0
        and not grid.found_enemy
    ):
        # Sense.
        pos = grid.current_pos
        target = grid.enemy_pos

        # Decide: try Q4 first.
        direction = next_step_toward(
            pos,
            target,
            grid.obstacles,
            grid.facing,
        )

        if planned_path:
            direction = planned_path.popleft()
        else:
            dx, dy = direction.delta
            next_pos = (pos[0] + dx, pos[1] + dy)

            greedy_valid = (
                not grid.is_blocked(*next_pos)
                and distance(next_pos, target) < distance(pos, target)
            )

            if not greedy_valid and not unreachable:
                planned_path = escape_path(pos, target)
                unreachable = not planned_path
                if planned_path:
                    direction = planned_path.popleft()

        # Act: align the heading, then attempt one forward move.
        dx, dy = grid.facing.delta
        if direction.delta == (-dy, dx):
            grid.turn_left()
        else:
            while grid.facing != direction:
                grid.turn_right()

        grid.move_forward()
        steps += 1
        visited.add(grid.current_pos)

    success = bool(grid.found_enemy)

    return {
        "steps": steps,
        "collisions": grid.collision_count - initial_collisions,
        "visited_count": len(visited),
        "found_enemy": success,
        "success": success,
    }


def report_to_json(stats):
    import json

    return json.dumps(
        stats,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    )


# ---------------------------------------------------------------------------
# Bonus：BFS 全局最短路（题面 Bonus·BFS 语义与排行榜）
# ---------------------------------------------------------------------------
def bfs_path_length(start, target, obstacles):
    """TODO(Bonus)：BFS 全局最短路步数；返回语义与边界职责见题面 Bonus 规范。"""
    raise NotImplementedError("Bonus bfs_path_length")


# ---------------------------------------------------------------------------
# 渲染（已提供，demo 专用，不进测试）
# ---------------------------------------------------------------------------
def render_frame(grid, trail=()):
    """ASCII 渲染一帧战场；trail 为走过的格子集合。返回 list[str]。"""
    trail = set(trail)
    rows = []
    for y in range(grid.height - 1, -1, -1):
        row = []
        for x in range(grid.width):
            if (x, y) == grid.current_pos:
                row.append("◉")
            elif (x, y) == grid.enemy_pos:
                row.append("▲")
            elif (x, y) in grid.obstacles:
                row.append("█")
            elif (x, y) in trail:
                row.append("·")
            else:
                row.append(".")
        rows.append("".join(row))
    return rows
