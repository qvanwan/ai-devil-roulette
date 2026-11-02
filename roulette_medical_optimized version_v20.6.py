import requests, time, random, re, json

print("💀 ====== 《AI 恶魔轮盘赌：v20.6 Pro 伤害膨胀版》 ====== 💀")
API_KEY = input("请粘贴你的智谱 API Key：").strip()
URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
MODEL = "glm-4-flash"
total_tokens = 0

ITEM_POOL = [
    "放大镜", "香烟", "手铐", "啤酒", "手锯", "逆转器", "过期药品", "肾上腺素", "一次性手机", "干扰器", 
    "防爆盾", "灭火器", "榴弹发射器", "诅咒娃娃", "防弹插板", "幸运硬币", "洗牌机", "除颤器", "命运轮盘", "闪光弹",
    "调换枪栓", "契约同盟", "债务清算",
    "强效肾上腺素", "纳米急救箱", "战术医疗舱", "双发扳机",
    "医疗箱", "万能解药" 
]

BULLET_TYPES = ["实弹", "空包弹", "高压实弹", "龙息弹", "麻醉弹", "吸血鬼弹", "玻璃弹", "穿甲弹", "瘟疫弹", "魔术弹", "混沌弹", "荆棘弹", "钝伤弹", "霰弹", "医疗弹", "反转弹"]

B_LIVE = "实弹"
B_BLANK = "空包弹"
B_HIGH = "高压实弹"
B_DRAGON = "龙息弹"
B_ANESTHETIC = "麻醉弹"
B_VAMPIRE = "吸血鬼弹"
B_GLASS = "玻璃弹"
B_PIERCE = "穿甲弹"
B_PLAGUE = "瘟疫弹"
B_MAGIC = "魔术弹"
B_CHAOS = "混沌弹"
B_THORN = "荆棘弹"
B_BLUNT = "钝伤弹"
B_SHOTGUN = "霰弹"
B_MEDICAL = "医疗弹"
B_REVERSE = "反转弹"
B_UNKNOWN = "未知"

BULLET_WEIGHTS = [
    (B_BLANK, 30), (B_LIVE, 20), (B_HIGH, 8), (B_DRAGON, 8), (B_ANESTHETIC, 4), 
    (B_VAMPIRE, 4), (B_GLASS, 4), (B_PIERCE, 4), (B_PLAGUE, 4), (B_SHOTGUN, 4), 
    (B_CHAOS, 3), (B_MAGIC, 2), (B_THORN, 1), (B_BLUNT, 1), (B_MEDICAL, 3), (B_REVERSE, 3)
]

contract_used_globally = 0
contract_alive = False

class Player:
    def __init__(self, name):
        self.name = name
        self.hp = 8       
        self.max_hp = 16  
        self.items = []     
        self.alive = True
        self.skip_turns = 0 
        self.sawed = False
        self.burning = False   
        self.has_shield = False 
        self.has_plate = False 
        self.has_defib = False 
        self.cursed = False    
        self.coin_count = 0 
        self.blocked = False 
        self.blinded = False 
        self.disarmed = False 
        self.overdose = False 
        self.healing_fog = False 
        self.reversed_turn = False 
        self.next_shot_buff = 0 
        self.double_shot = False 
        self.known_next = B_UNKNOWN 
        self.ally = None 

players = [Player(f"玩家{x}") for x in "ABCDEF"]
alive_players = players.copy()

def ask_ai(sys_prompt, msg):
    global total_tokens
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    data = {"model": MODEL, "messages": [{"role": "system", "content": sys_prompt}, {"role": "user", "content": msg}], "temperature": 0.7, "max_tokens": 60}
    try:
        res = requests.post(URL, headers=headers, json=data, timeout=10)
        if res.status_code == 200:
            resp_json = res.json()
            if 'usage' in resp_json:
                total_tokens += resp_json['usage'].get('total_tokens', 0)
            return resp_json['choices'][0]['message']['content'].strip()
        return '{"action": "shoot", "target": "自己"}'
    except Exception:
        return '{"action": "shoot", "target": "自己"}'

def sync_memory(target, bullet):
    target.known_next = bullet
    if target.ally:
        target.ally.known_next = bullet
        print(f"  🔗 【同盟共享】底牌情报已同步给盟友 {target.ally.name}！")

def clear_all_memories():
    for p in alive_players:
        p.known_next = B_UNKNOWN
    print("  🧠 物理顺序改变，所有人的私有记忆被强制清空！")

def load_chamber():
    total = random.randint(6, 12)
    chamber = []
    bullets, weights = zip(*BULLET_WEIGHTS)
    for _ in range(total):
        chamber.append(random.choices(bullets, weights=weights, k=1)[0])
    random.shuffle(chamber)
    return chamber

def next_bullet_type(bullet):
    if bullet == B_BLANK: return B_LIVE
    else: return B_BLANK

def deal_items(alive_players, round_num):
    item_count = 2 if round_num == 1 else 3
    for p in alive_players:
        given = []
        if p.hp == 1: extra = 3; buff_text = " (濒死狂化+3)"
        elif p.hp <= 2: extra = 2; buff_text = " (重度残血+2)"
        elif p.hp <= 4: extra = 1; buff_text = " (轻度残血+1)"
        else: extra = 0; buff_text = ""
            
        actual_count = item_count + extra 
        for _ in range(actual_count):
            if len(p.items) < 8:
                it = random.choice(ITEM_POOL)
                p.items.append(it)
                given.append(it)
        if given:
            print(f"  🎁 {p.name} 摸到{buff_text}：{', '.join(given)}")

def handle_death(p):
    global contract_alive
    if p.hp <= 0:
        if p.has_defib:
            p.hp = 1
            p.has_defib = False
            print(f"  ⚡ 【除颤器】启动！{p.name} 免疫了致命伤害，并恢复了 1 点生命！")
        else:
            print(f"  💀 【{p.name}】倒下了！")
            if p in alive_players: alive_players.remove(p)
            
            if p.ally and p.ally in alive_players:
                p.ally.hp = 0
                print(f"  📜 【契约同盟】破裂！{p.name} 的死亡导致盟友 {p.ally.name} 当场陪葬！")
                if p.ally in alive_players: alive_players.remove(p.ally)
                contract_alive = False

def apply_defense_and_damage(shooter, target, base_dmg, bullet_name):
    if bullet_name in [B_PIERCE, B_CHAOS]:
        print(f"  🗡️ 【{bullet_name}】无视了所有防具，造成真实伤害！")
        if base_dmg > 0:
            target.hp -= base_dmg
            print(f"  🩸 {target.name} 受到 {base_dmg} 点真实伤害 (HP: {target.hp})")
        return True 

    if target.has_shield:
        if bullet_name == B_HIGH and shooter.sawed:
            print(f"  🛡️💥 【防爆盾】被锯短的高压实弹直接击穿，完全失效！")
        else:
            base_dmg = max(0, base_dmg - 1)
            target.has_shield = False
            print(f"  🛡️ 【防爆盾】抵消了 1 点伤害！")
            if base_dmg == 0:
                print(f"  ✅ {target.name} 的护盾完全挡下了攻击！")
                return False 
    
    if target.has_plate and (target.hp - base_dmg <= 0):
        print(f"  🛡️🩹 【防弹插板】触发！强行抵挡了致命伤害！")
        base_dmg = max(0, base_dmg - 1) 
        target.has_plate = False
        if target.hp - base_dmg <= 0:
            target.hp = 1
            print(f"  🩸 锁血存活！{target.name} 保留 1 点生命！")
        else:
            target.hp -= base_dmg
        return True

    if base_dmg > 0:
        target.hp -= base_dmg
        print(f"  🩸 {target.name} 受到 {base_dmg} 点伤害 (HP: {target.hp})")
    
    return True 

def resolve_damage(shooter, target, bullet, sawed, extra_dmg=0, is_splash=False, is_launcher=False):
    global dmg_bonus 
    
    if bullet == B_BLANK:
        print(f"  💨 【空包弹】无伤害。")
        if not is_splash: shooter.sawed = False
        return False 

    if bullet == B_MAGIC:
        if is_splash: return True
        print(f"  🎩 【魔术弹】命中了 {target.name}！变魔术了！")
        shooter.items, target.items = target.items, shooter.items
        print(f"  🔄 {shooter.name} 和 {target.name} 完全交换了手牌！")
        if shooter.sawed: shooter.sawed = False
        return True

    if bullet == B_MEDICAL:
        print(f"  💉 【医疗弹】炸开，产生了治疗雾！")
        if target in alive_players:
            idx = alive_players.index(target)
            targets_to_heal = [alive_players[(idx - 1) % len(alive_players)], target, alive_players[(idx + 1) % len(alive_players)]]
            for p in set(targets_to_heal):
                p.hp = min(p.max_hp, p.hp + 1)
                p.healing_fog = True
                print(f"    🩹 {p.name} 沐浴治疗雾，回复 1 点生命 (HP: {p.hp})，下回合将再回复 1 点。")
        return True

    if bullet == B_REVERSE:
        print(f"  🌀 【反转弹】命中了 {target.name}，思维被扭曲！")
        target.reversed_turn = True
        return True

    base_dmg = 1
    if bullet == B_HIGH: base_dmg = 2
    elif bullet in [B_ANESTHETIC, B_VAMPIRE]: base_dmg = 0 if bullet != B_VAMPIRE else 1
    elif bullet == B_CHAOS: base_dmg = random.randint(1, 4)
    
    if base_dmg > 0:
        base_dmg += dmg_bonus
        
    total_dmg = base_dmg + (1 + dmg_bonus if sawed else 0) + extra_dmg
    if bullet in [B_ANESTHETIC, B_VAMPIRE, B_CHAOS, B_SHOTGUN]: total_dmg = base_dmg + extra_dmg

    if bullet == B_GLASS:
        if sawed: total_dmg = 2 + dmg_bonus
        else: total_dmg = 1 + dmg_bonus
        
    print(f"  💥 【{bullet}】命中了 {target.name}！" + (f" (基础伤害+{dmg_bonus})" if dmg_bonus > 0 and base_dmg > 0 else ""))
    
    trigger_splash = False
    if bullet == B_GLASS and not is_launcher: 
        if target.has_shield or (target.has_plate and not is_splash):
            trigger_splash = True
            print(f"  💎 玻璃弹击中了防御装备，玻璃碎片炸裂了！")

    is_blunt_kill = False
    if bullet == B_BLUNT:
        if target.hp - total_dmg <= 0:
            is_blunt_kill = True
            print(f"  🔨 【钝伤弹】重击！目标本该阵亡，但被强制锁血至 1 点！")
            target.hp = 1
            target.has_shield = False
            target.has_plate = False
            target.has_defib = False
            if target.items:
                lost = target.items.pop(random.randrange(len(target.items)))
                print(f"  💥 冲击力震碎了 {target.name} 的【{lost}】和所有防御装备！")
        else:
            apply_defense_and_damage(shooter, target, total_dmg, bullet)

    damage_applied = False
    if not is_blunt_kill and bullet != B_BLUNT:
        damage_applied = apply_defense_and_damage(shooter, target, total_dmg, bullet)
    elif is_blunt_kill:
        damage_applied = True

    if trigger_splash and not is_splash:
        for p in list(alive_players):
            if p != target and p != shooter: 
                print(f"  💎 玻璃碎片飞溅向了 {p.name}！")
                apply_defense_and_damage(shooter, p, 1 + dmg_bonus, "玻璃碎片")

    if bullet == B_DRAGON and damage_applied:
        target.burning = True
        print(f"  🔥 {target.name} 开始燃烧，下回合将受到 1 点持续伤害！")
    elif bullet == B_VAMPIRE:
        shooter.hp = min(shooter.max_hp, shooter.hp + 1)
        print(f"  🧛 吸血鬼弹触发！{shooter.name} 恢复了 1 点生命 (HP: {shooter.hp})")
    elif bullet == B_ANESTHETIC:
        if target.items:
            lost = target.items.pop(random.randrange(len(target.items)))
            print(f"  💤 麻醉弹触发！{target.name} 陷入昏睡，随机丢失了【{lost}】！")
    elif bullet == B_PLAGUE:
        target.blocked = True
        print(f"  ☣️ 瘟疫弹触发！{target.name} 感染了瘟疫，下回合无法使用任何道具！")
    elif bullet == B_THORN:
        shooter.hp -= (1 + dmg_bonus)
        print(f"  🌵 荆棘弹反噬！开枪者 {shooter.name} 受到 {1+dmg_bonus} 点反伤 (HP: {shooter.hp})")
    elif bullet == B_SHOTGUN and not is_splash and not is_launcher:
        print(f"  💥 【霰弹】炸开！全场所有玩家无差别受到 {1+dmg_bonus} 点伤害！")
        for p in list(alive_players):
            if p != target:
                print(f"    💥 霰弹波及了 {p.name}：")
                apply_defense_and_damage(shooter, p, 1 + dmg_bonus, "霰弹碎片")

    targets_to_check = [target, shooter] if bullet == B_THORN else [target]
    if bullet == B_SHOTGUN and not is_splash and not is_launcher: targets_to_check = list(alive_players)
    if trigger_splash and not is_splash: targets_to_check += [x for x in alive_players if x != target and x != shooter]

    for p in set(targets_to_check):
        handle_death(p)
                
    if not is_splash: shooter.sawed = False
    return True 

round_num = 1
dmg_bonus = 0
chamber = load_chamber()
print(f"\n💥 【第一轮装填】上帝视角弹匣序列：{chamber}")
deal_items(alive_players, round_num)

while len(alive_players) > 1:
    if len(alive_players) == 2:
        p1, p2 = alive_players[0], alive_players[1]
        if p1.ally == p2 and p2.ally == p1:
            print(f"\n👑 场上仅剩下结盟的【{p1.name}】和【{p2.name}】，他们无法互相攻击，同盟共同获得最终胜利！")
            break

    for p in alive_players:
        if len(alive_players) == 2:
            p1, p2 = alive_players[0], alive_players[1]
            if p1.ally == p2 and p2.ally == p1:
                break

        if not p.ally: p.known_next = B_UNKNOWN
        
        if not chamber:
            round_num += 1
            dmg_bonus = round_num // 10
            
            chamber = load_chamber()
            print(f"\n💥 【换弹】第 {round_num} 轮，上帝视角弹匣序列：{chamber}")
            
            # 【彻底修复文案误解】只有当轮数是10的倍数时，才提示一次伤害提升
            if round_num % 10 == 0:
                print(f"🔥 【武器过热】环境恶化：从第 {round_num} 轮起，所有造成伤害的子弹与手锯加成提升至 {dmg_bonus} 点！")
                
            for alive_p in alive_players:
                if not alive_p.ally: alive_p.known_next = B_UNKNOWN
                alive_p.sawed = False
                alive_p.has_shield = False
                alive_p.has_plate = False
            deal_items(alive_players, round_num)
                
        current = alive_players[0]
        is_blocked_this_turn = current.blocked
        is_disarmed_this_turn = current.disarmed
        is_reversed_this_turn = current.reversed_turn
        current.blocked = False
        current.disarmed = False
        current.reversed_turn = False

        if current.burning:
            current.hp -= 1
            print(f"🔥 回合开始，【{current.name}】受到龙息灼烧，扣除 1 点生命 (HP: {current.hp})")
            current.burning = False
            handle_death(current)
            if current not in alive_players: continue

        if current.overdose:
            current.hp -= 2
            print(f"💔 回合开始，【{current.name}】受到【强效肾上腺素】反噬，扣除 2 点生命 (HP: {current.hp})")
            current.overdose = False
            handle_death(current)
            if current not in alive_players: continue

        if current.healing_fog:
            current.hp = min(current.max_hp, current.hp + 1)
            print(f"🩹 回合开始，【{current.name}】受到医疗雾持续治疗，恢复 1 点生命 (HP: {current.hp})")
            current.healing_fog = False

        if current.skip_turns > 0:
            print(f"⛓️ 【{current.name}】被控，跳过本回合！")
            current.skip_turns -= 1
            alive_players.append(alive_players.pop(0)) 
            continue

        print(f"\n========== 轮到【{current.name}】(HP: {current.hp}/{current.max_hp}) ==========")
        if is_reversed_this_turn: print(f"🌀 【{current.name}】受到反转弹影响，本回合所有指令将反向执行！")
        if is_blocked_this_turn: print(f"☣️ 【{current.name}】处于瘟疫封锁状态，本回合只能开枪！")
        if is_disarmed_this_turn: print(f"🚫 【{current.name}】被缴械，本回合只能使用道具！")
        if current.blinded: print(f"😵 【{current.name}】被闪光弹致盲，下一枪必定打空！")
        print(f"🔫 剩余子弹：{len(chamber)} | 🎒 道具：{current.items}")
        if current.ally: print(f"🔗 你的盟友：{current.ally.name}")
        
        retry = 0
        action_taken = False
        while not action_taken and retry < 2:
            other_names = [x.name for x in alive_players if x != current and x != current.ally]
            if not other_names: other_names = ["自己"]
            
            if is_blocked_this_turn:
                item_prompt = "你被瘟疫封锁了，本回合【绝对不能使用任何道具】，只能开枪！"
            elif is_disarmed_this_turn:
                item_prompt = "你被缴械了，本回合【绝对不能开枪】，只能使用道具！"
            else:
                item_prompt = f"可用道具：{current.items}" if current.items else "你没有任何道具！只能开枪！"
                if not current.burning and "灭火器" in current.items:
                    item_prompt += " (你身上没火，不能用灭火器！)"
                if current.has_defib and "防弹插板" in current.items:
                    item_prompt += " (你有除颤器，无法再装插板！)"
                if current.has_plate and "除颤器" in current.items:
                    item_prompt += " (你有插板，无法再装除颤器！)"
                if current.has_plate and "防弹插板" in current.items:
                    item_prompt += " (你身上已有插板，不能再装插板！)"
                if current.has_defib and "除颤器" in current.items:
                    item_prompt += " (你身上已有除颤器，不能再装除颤器！)"

            private_info = f"你的私有记忆：你确切知道下一发是【{current.known_next}】。" if current.known_next != B_UNKNOWN else "你的私有记忆：你不知道下一发是什么。"
            
            prompt = f"""你是{current.name}。HP:{current.hp}。
{item_prompt}
状态：枪管{"已锯短" if current.sawed else "正常"} | 护盾：{"有" if current.has_shield else "无"} | 插板：{"有" if current.has_plate else "无"}
{private_info}
其他存活敌人：{other_names}
注意：绝对不能攻击你的盟友！底牌子弹（如麻醉弹、实弹）只是子弹，绝不能用道具动作使用它。

请输出行动，严格JSON：
1. 用道具：{{"action": "use", "item": "你想用的具体道具中文名"}}
2. 开枪：{{"action": "shoot", "target": "目标名"}} (自己或玩家名)"""

            ans = ask_ai("你是老千赌徒。只输出JSON。", prompt)
            try:
                act = json.loads(re.search(r'\{.*\}', ans, re.DOTALL).group())
            except Exception:
                act = {"action": "shoot", "target": "自己"}

            if act.get("action") == "use" and not is_blocked_this_turn:
                item = act.get("item", "").strip()
                
                if item in BULLET_TYPES:
                    print(f"  ⚠️ {current.name} 产生幻觉，试图把子弹【{item}】当道具用，系统强制打回！")
                    retry += 1
                    continue

                if item not in current.items:
                    print(f"⚠️ 你没有[{item}]，强制转移目标开枪！")
                    act = {"action": "shoot", "target": random.choice(other_names)}
                else:
                    if item == "灭火器" and not current.burning:
                        print(f"  ⚠️ {current.name} 试图在没火的时候使用灭火器，系统没收了该道具！")
                        current.items.remove(item)
                        retry += 1
                        continue
                    if item == "防弹插板" and current.has_defib:
                        print(f"  ⚠️ {current.name} 已有除颤器，无法同时装备防弹插板！")
                        retry += 1
                        continue
                    if item == "防弹插板" and current.has_plate:
                        print(f"  ⚠️ {current.name} 身上已经安装了防弹插板，无法重复安装！")
                        retry += 1
                        continue
                    if item == "除颤器" and current.has_plate:
                        print(f"  ⚠️ {current.name} 已有防弹插板，无法同时装备除颤器！")
                        retry += 1
                        continue
                    if item == "除颤器" and current.has_defib:
                        print(f"  ⚠️ {current.name} 身上已经装备了除颤器，无法重复装备！")
                        retry += 1
                        continue

                    current.items.remove(item)
                    
                    if is_reversed_this_turn:
                        print(f"  🌀 【反转发作】{current.name} 原本想使用【{item}】，结果动作被扭曲！")
                        if item in ["香烟", "纳米急救箱", "战术医疗舱", "强效肾上腺素", "过期药品", "医疗箱", "万能解药"]:
                            current.hp -= 2 
                            print(f"    🤮 医疗道具变成了剧毒！{current.name} 扣除 2 点生命 (HP: {current.hp})")
                        elif item == "榴弹发射器":
                            print(f"    💥 榴弹炸膛了！{current.name} 试图发射榴弹，结果炸伤自己，扣除 2 点真实伤害！")
                            current.hp -= 2
                        elif item == "双发扳机":
                            print(f"    🔫 扳机走火！{current.name} 双发扳机走火，打中自己腿部，扣除 1 点生命。")
                            current.hp -= 1
                        elif item in ["债务清算", "肾上腺素"]:
                            print(f"    💥 {current.name} 试图使用【{item}】，结果作用在了自己身上！")
                            current.hp -= 1
                        else:
                            print(f"    🚫 {current.name} 试图使用【{item}】，但装备失败，道具浪费。")
                        handle_death(current)
                        if current not in alive_players: action_taken = True
                        continue 

                    print(f"  🛠️ {current.name} 使用了【{item}】")
                    
                    if item == "强效肾上腺素":
                        current.hp = min(current.max_hp, current.hp + 3)
                        current.overdose = True
                        current.next_shot_buff += 1
                        print(f"💉 猛药强心！{current.name} HP恢复到 {current.hp}，下回合将受到反噬，且下一枪伤害+1！")
                    elif item == "纳米急救箱":
                        if current.hp <= 4:
                            current.hp = min(current.max_hp, current.hp + 3)
                            print(f"📦 绝境急救！{current.name} 触发高额回复，HP恢复到 {current.hp}")
                        else:
                            current.hp = min(current.max_hp, current.hp + 1)
                            print(f"📦 常规急救！{current.name} 仅回复了 1 点生命 (HP: {current.hp})")
                    elif item == "战术医疗舱":
                        current.hp = min(current.max_hp, current.hp + 3) 
                        current.has_shield = True
                        print(f"🩹 战地急救！{current.name} HP恢复到 {current.hp}，并获得一层防爆盾！")
                    elif item == "医疗箱":
                        current.hp = min(current.max_hp, current.hp + 4) 
                        print(f"🧰 开启医疗箱！{current.name} 大量回血，HP恢复到 {current.hp}")
                    elif item == "万能解药":
                        current.hp = min(current.max_hp, current.hp + 2) 
                        current.burning = False
                        current.blocked = False
                        current.reversed_turn = False
                        current.overdose = False
                        print(f"🧪 万能解药！{current.name} 恢复了 2 点生命，并清除了所有异常状态 (HP: {current.hp})")
                    elif item == "双发扳机":
                        current.double_shot = True
                        print(f"🔫 双发扳机！{current.name} 准备好本回合打出两发子弹！")
                    elif item == "香烟": 
                        current.hp = min(current.max_hp, current.hp + 2) 
                        print(f"🚬 抽了根好烟，HP恢复到 {current.hp}")
                    elif item == "灭火器": 
                        current.burning = False
                        print(f"🧯 扑灭了火焰！")
                    elif item == "防爆盾": 
                        current.has_shield = True
                        print("🛡️ 获得了一层防爆盾！")
                    elif item == "防弹插板": 
                        current.has_plate = True
                        print("🩹 安装了防弹插板！(致命伤锁血1点)")
                    elif item == "除颤器": 
                        current.has_defib = True
                        print("⚡ 装备了除颤器！(受到致命伤时起死回生恢复1血)")
                    elif item == "闪光弹":
                        targets = [x for x in alive_players if x != current]
                        if targets:
                            tgt = random.choice(targets)
                            tgt.blinded = True
                            print(f"💥 闪光弹爆开！{tgt.name} 被致盲，下一枪必定打空！")
                    elif item == "契约同盟":
                        if contract_used_globally >= 2 or contract_alive:
                            print("❌ 契约同盟无法使用，道具被销毁！")
                            continue
                        else:
                            targets = [x for x in alive_players if x != current]
                            if targets:
                                tgt = random.choice(targets)
                                print(f"🤝 {current.name} 向 {tgt.name} 发起了契约同盟邀请！")
                                invite_prompt = f"你是{tgt.name}。玩家 {current.name} 邀请你结盟（同生共死，不可互相攻击）。你当前血量{tgt.hp}，对方血量{current.hp}。请严格输出 JSON：{{\"accept\": true}} 或 {{\"accept\": false}}。"
                                ans_invite = ask_ai("请决定是否结盟。", invite_prompt)
                                accept = "true" in ans_invite.lower()
                                contract_used_globally += 1
                                if accept:
                                    current.ally = tgt
                                    tgt.ally = current
                                    contract_alive = True
                                    current.known_next = tgt.known_next
                                    print(f"✅ {tgt.name} 同意了结盟！双方达成生死契约！")
                                else:
                                    print(f"❌ {tgt.name} 拒绝了结盟请求！")
                    elif item == "债务清算":
                        targets = [x for x in alive_players if x != current]
                        if targets:
                            tgt = random.choice(targets)
                            stolen = False
                            for buff in ["has_shield", "has_plate", "has_defib"]:
                                if getattr(tgt, buff):
                                    setattr(current, buff, True)
                                    setattr(tgt, buff, False)
                                    stolen = True
                            if stolen: 
                                print(f"⚖️ 债务清算！{current.name} 扒光了 {tgt.name} 的所有防御装备！")
                                if any(getattr(current, b) for b in ["has_shield", "has_plate", "has_defib"]):
                                    print(f"  🛡️ {current.name} 现在获得了对方的防御保护（来自债务清算）！")
                            else:
                                tgt.hp -= 1
                                print(f"⚖️ 债务清算！{tgt.name} 没有防御装，被强行扣除 1 血 (HP: {tgt.hp})")
                                handle_death(tgt)
                    elif item == "调换枪栓":
                        if len(chamber) > 1:
                            top_bullet = chamber.pop(0)
                            chamber.append(top_bullet)
                            print(f"🔄 调换枪栓！将第一发子弹抽出来，塞到了弹匣的最底部！")
                            clear_all_memories()
                        else: 
                            print(f"🔄 子弹太少，调换枪栓没起作用。")
                    elif item == "幸运硬币": 
                        current.coin_count += 1
                        print(f"🪙 抛起了一枚幸运硬币（当前蓄力：{current.coin_count} 枚），下一枪定生死！")
                    elif item == "洗牌机": 
                        random.shuffle(chamber)
                        print("🌪️ 使用了洗牌机，枪膛内的子弹顺序被彻底打乱！")
                        clear_all_memories()
                    elif item == "命运轮盘":
                        print("🎰 拨动了命运轮盘...")
                        pool = [x for x in ITEM_POOL if x not in ["命运轮盘", "除颤器", "洗牌机"]]
                        reward = random.choice(pool + ["回血", "扣血"])
                        if reward == "回血":
                            current.hp = min(current.max_hp, current.hp + 1)
                            print(f"  🎁 轮盘指针停在了【恢复1血】！当前 HP: {current.hp}")
                        elif reward == "扣血":
                            current.hp -= 2
                            print(f"  💀 轮盘指针停在了【受到2点伤害】！当前 HP: {current.hp}")
                            handle_death(current)
                            if current not in alive_players: action_taken = True
                        else:
                            current.items.append(reward)
                            print(f"  🎁 轮盘指针停在了【{reward}】！获得该道具。")
                    elif item == "过期药品":
                        if random.random() < 0.4: 
                            current.hp = min(current.max_hp, current.hp + 2)
                            print(f"💊 赌赢了！HP恢复到 {current.hp}")
                        else:
                            current.hp -= 1
                            print(f"🤮 药效变质！扣除1血 (HP: {current.hp})")
                            handle_death(current)
                            if current not in alive_players: action_taken = True
                    elif item in ["放大镜", "一次性手机"]:
                        if item == "放大镜": 
                            sync_memory(current, chamber[0] if chamber else B_UNKNOWN)
                        else:
                            idx = random.randrange(len(chamber))
                            sync_memory(current, chamber[idx] if len(chamber)>0 else B_UNKNOWN)
                        print(f"🔍 玩家 {current.name} 偷偷查看了底牌，下一发是【{current.known_next}】（其他玩家不知道）。")
                    elif item == "啤酒":
                        if chamber:
                            eject = chamber.pop(0)
                            print(f"🍺 退出一发子弹！剩余 {len(chamber)} 发")
                    elif item == "逆转器":
                        if chamber:
                            old_b = chamber[0]
                            chamber[0] = next_bullet_type(old_b)
                            if current.known_next != B_UNKNOWN: 
                                sync_memory(current, next_bullet_type(current.known_next))
                            print(f"🔄 逆转了子弹！")
                    elif item == "手锯": 
                        current.sawed = True
                        print("🪚 枪管已锯短！")
                    elif item in ["手铐", "干扰器"]:
                        valid_targets = [x for x in alive_players if x != current and x.skip_turns == 0]
                        if valid_targets:
                            tgt = random.choice(valid_targets)
                            tgt.skip_turns += 1
                            print(f"⛓️ 控住了 {tgt.name}！")
                        else: 
                            print("⚠️ 无人可铐，道具浪费。")
                    elif item == "肾上腺素":
                        targets = [x for x in alive_players if x != current and x.items]
                        if targets:
                            victim = random.choice(targets)
                            stolen = victim.items.pop(random.randrange(len(victim.items)))
                            current.items.append(stolen)
                            print(f"💉 从 {victim.name} 手中抢走了【{stolen}】")
                        else: 
                            print("💉 抢了个寂寞。")
                    elif item == "诅咒娃娃":
                        targets = [x for x in alive_players if x != current]
                        if targets:
                            tgt = random.choice(targets)
                            if not tgt.cursed: 
                                tgt.cursed = True
                                print(f"🧸 给 {tgt.name} 种下了诅咒娃娃！下一枪将随机索敌！")
                            else: 
                                print(f"⚠️ {tgt.name} 身上已经有娃娃了，无法叠加。")
                    elif item == "榴弹发射器":
                        if chamber:
                            bullet = chamber.pop(0)
                            print(f"🚀 {current.name} 发射了榴弹！消耗了一发【{bullet}】！")
                            
                            extra_dmg = 0
                            if current.coin_count > 0:
                                for _ in range(current.coin_count):
                                    if random.choice([True, False]): 
                                        print(f"  🪙 【幸运硬币】正面！本次伤害 +2！")
                                        extra_dmg += 2
                                    else:
                                        current.hp -= 2
                                        print(f"  🪙 【幸运硬币】背面！天罚反噬无视任何防御，扣除 2 血 (HP: {current.hp})")
                                        handle_death(current)
                                        if current not in alive_players: 
                                            action_taken = True
                                            break 
                                current.coin_count = 0
                                if current not in alive_players: break 
                            
                            for tgt in list(alive_players):
                                if tgt != current: 
                                    print(f"  💥 榴弹波及了 {tgt.name}：")
                                    resolve_damage(current, tgt, bullet, current.sawed, extra_dmg, is_launcher=True)
                            current.sawed = False
                            if not current.ally: current.known_next = B_UNKNOWN
                            action_taken = True 
                        else: 
                            print("⚠️ 枪膛空空，榴弹发射器无法使用。")
                    
                    if current.hp <= 0 and current in alive_players:
                        handle_death(current)
                        if current not in alive_players: action_taken = True
                    continue 
            
            if (act.get("action") == "shoot" or is_blocked_this_turn) and not is_disarmed_this_turn:
                tgt_name = act.get("target", "自己") if act.get("action") == "shoot" else "自己"
                
                if current.cursed:
                    target = random.choice(alive_players)
                    print(f"  🧸 【诅咒娃娃】发作！开枪动作被强行扭曲！")
                    current.cursed = False
                else:
                    target = current if "自己" in tgt_name or current.name in tgt_name else next((x for x in alive_players if x.name in tgt_name), current)
                
                if is_reversed_this_turn and target != current:
                    print(f"  🌀 【反转发作】{current.name} 原本想打 {target.name}，结果枪口强行对准了自己！")
                    target = current

                if target.ally == current and target != current:
                    print(f"  🔗 【同盟限制】你无法攻击盟友 {target.name}！系统强制将目标改为自己作为惩罚！")
                    target = current
                
                bullet = chamber.pop(0) if chamber else B_BLANK
                print(f"  💥 {current.name} 朝【{target.name}】扣动了扳机...")
                action_taken = True
                
                if current.blinded:
                    print(f"  😵 【闪光弹】效果发作！{current.name} 双眼发白，打出的子弹如同空包弹！")
                    bullet = B_BLANK
                    current.blinded = False
                
                was_sawed = current.sawed 
                current.sawed = False 
                
                extra_dmg = 0
                if current.coin_count > 0:
                    for _ in range(current.coin_count):
                        if random.choice([True, False]): 
                            print(f"  🪙 【幸运硬币】正面！本次伤害 +2！")
                            extra_dmg += 2
                        else:
                            current.hp -= 2
                            print(f"  🪙 【幸运硬币】背面！天罚反噬无视任何防御，扣除 2 血 (HP: {current.hp})")
                            handle_death(current)
                            if current not in alive_players:
                                break 
                    current.coin_count = 0
                    if current not in alive_players:
                        action_taken = True
                        break 
                
                extra_dmg += current.next_shot_buff
                current.next_shot_buff = 0

                def fire_single(bullet_type, target_obj):
                    if bullet_type == B_BLANK:
                        print(f"  💨 【空包弹】无伤害。")
                        return False
                    else:
                        resolve_damage(current, target_obj, bullet_type, was_sawed, extra_dmg)
                        return True

                fire_single(bullet, target)

                if current.double_shot and current in alive_players:
                    current.double_shot = False
                    print(f"  🔫 【双发扳机】触发，强制打出第二发子弹！")
                    
                    target2 = target
                    if target not in alive_players:
                        target2 = current
                        print(f"  🎯 第一发目标已阵亡，第二发子弹强制射向自己！")
                        
                    bullet2 = chamber.pop(0) if chamber else B_BLANK
                    fire_single(bullet2, target2)

                if bullet == B_BLANK and target == current and not current.cursed:
                    print(f"  🔄 自轰空包，【{current.name}】连击！")
                    action_taken = False 
                    if not chamber: break
                    continue 
                else:
                    if not current.ally: current.known_next = B_UNKNOWN
                break 

        if not action_taken:
            print(f"🚨 【{current.name}】思考超时或连续违规！")
            if is_disarmed_this_turn:
                print(f"  🚫 玩家 {current.name} 被缴械且无合法道具，强行跳过本回合。")
                action_taken = True
            else:
                print(f"  系统强行剥夺回合，强制向敌人开枪！")
                if chamber:
                    bullet = chamber.pop(0)
                    target = random.choice([x for x in alive_players if x != current and x != current.ally])
                    print(f"  💥 {current.name} 朝【{target.name}】扣动了扳机...")
                    extra_dmg = 0
                    if current.coin_count > 0:
                        for _ in range(current.coin_count):
                            if random.choice([True, False]): 
                                print(f"  🪙 【幸运硬币】正面！本次伤害 +2！")
                                extra_dmg += 2
                            else:
                                current.hp -= 2
                                print(f"  🪙 【幸运硬币】背面！天罚反噬无视任何防御，扣除 2 血 (HP: {current.hp})")
                                handle_death(current)
                                break 
                        current.coin_count = 0
                    
                    if current in alive_players:
                        resolve_damage(current, target, bullet, current.sawed, extra_dmg)
                        current.sawed = False
                        if not current.ally: current.known_next = B_UNKNOWN
                action_taken = True

        if len(alive_players) <= 1: break
        
        if current.alive and current in alive_players and action_taken:
            alive_players.append(alive_players.pop(0))

    if len(alive_players) <= 1:
        break

print(f"\n👑 游戏结束！最终幸存者：【{alive_players[0].name if alive_players else '无'}】！")
print(f"💡 【账单】本局共消耗了 {total_tokens} 个 Token。")