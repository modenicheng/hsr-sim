from hsr_sim.models.db.user_characters import UserCharacter


class AppState:

    def __init__(self):
        self.current_user_id: int = 1  # 单用户默认
        self.selected_character: UserCharacter | None = None
        self.current_team: dict[int, UserCharacter | None] = {
            1: None,
            2: None,
            3: None,
            4: None
        }  # 当前队伍，键为位置（1-4），值为角色对象或 None
