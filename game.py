#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
《午间汉堡铺》v0.6
AI 玩家经营汉堡店：
- 12 位顾客
- 随机订单与前期防重复
- 清晰火候倒计时
- 翻面不再推进时间
- 中英文食材指令
- 第 5 天保证出现批量订单
- 总金币、今日累计收入、装修提醒
- 无限周目与本地存档
- 真实批量订单与托盘
- 原创配方、试吃与隐藏菜单
- 顾客专精透明评分与人物反应
- 招牌风格实际影响经营
- 出餐检查、撤销、清酱与顾客档案
"""

from __future__ import annotations
import json
import random
from pathlib import Path
from collections import Counter

BASE = Path(__file__).resolve().parent
SAVE_FILE = BASE / "save.json"

DAY_ORDER_COUNT = {1:5, 2:5, 3:6, 4:6, 5:7, 6:7, 7:8}

UNLOCKS = {
    1:["原味胚","牛肉饼","鸡肉饼","芝士","生菜","番茄","番茄酱"],
    2:["全麦胚","洋葱","酸黄瓜","蛋黄酱"],
    3:["培根","煎蛋"],
    4:["辣酱"],
    5:["双层汉堡","批量订单"],
    6:["隐藏菜单"],
    7:["唐九"],
}

RENOVATIONS = {
    "窗边花架":{"cost":80,"desc":"所有顾客耐心+1"},
    "暖色吊灯":{"cost":120,"desc":"每日结算声誉额外+1"},
    "招牌照片墙":{"cost":140,"desc":"摆放分最低保底8分"},
    "加宽操作台":{"cost":150,"desc":"组装不消耗回合"},
    "自动酱料机":{"cost":160,"desc":"加酱不消耗回合"},
    "高级烤台":{"cost":180,"desc":"烤位增加到3个"},
    "舒适候餐区":{"cost":220,"desc":"所有顾客耐心再+2"},
    "霓虹招牌":{"cost":260,"desc":"每单基础售价+2金币"},
}

CUSTOMERS = [
    {"name":"林野","patience":7,"focus":"speed","likes":["牛肉饼","芝士"],"dislikes":["洋葱"],"tip":1.1},
    {"name":"米娜","patience":10,"focus":"plating","likes":["番茄","芝士"],"dislikes":[],"tip":1.1},
    {"name":"阿栗","patience":12,"focus":"innovation","likes":["鸡肉饼","辣酱","酸黄瓜"],"dislikes":[],"tip":1.0},
    {"name":"周姨","patience":11,"focus":"accuracy","likes":["鸡肉饼","生菜","番茄"],"dislikes":["培根","辣酱"],"tip":1.0},
    {"name":"沈昼","patience":10,"focus":"portion","likes":["牛肉饼","煎蛋","芝士"],"dislikes":[],"tip":1.2},
    {"name":"诺亚","patience":10,"focus":"plating","likes":["全麦胚","鸡肉饼","生菜"],"dislikes":["蛋黄酱"],"tip":1.0},
    {"name":"蓁蓁","patience":8,"focus":"accuracy","likes":["鸡肉饼","煎蛋","生菜"],"dislikes":["培根","蛋黄酱"],"tip":1.0},
    {"name":"老曹","patience":9,"focus":"fire","likes":["牛肉饼"],"dislikes":[],"tip":1.1},
    {"name":"苏弥","patience":12,"focus":"accuracy","likes":["芝士","番茄酱"],"dislikes":["洋葱"],"tip":1.0},
    {"name":"罗宾","patience":6,"focus":"speed","likes":[],"dislikes":[],"tip":1.0},
    {"name":"伊芙","patience":11,"focus":"accuracy","likes":["全麦胚","生菜","番茄","洋葱","煎蛋"],"dislikes":["牛肉饼","鸡肉饼","培根"],"tip":1.0},
    {"name":"唐九","patience":9,"focus":"mystery","likes":[],"dislikes":[],"tip":1.3},
]

FOCUS_LABELS = {
    "speed":"出餐速度",
    "plating":"层次摆放",
    "innovation":"创意搭配",
    "accuracy":"订单准确度",
    "portion":"份量与饱腹感",
    "fire":"火候",
    "mystery":"隐藏菜单与未知规则",
}

SIGN_STYLE_EFFECTS = {
    "温馨":"高分订单的熟客关系成长更快。",
    "复古":"原创配方更容易通过试吃，正式菜单售价更高。",
    "极简":"完全正确的层次摆放获得额外奖励，但顾客耐心略低。",
    "怪诞":"创意试吃更容易得到好评，隐藏菜单奖励更高。",
}

CUSTOMER_REACTIONS = {
    "林野": {"high":"时间刚刚好。下次午休我还来。", "mid":"味道可以，再快一点就更好了。", "low":"我午休快结束了，这份先算了。"},
    "米娜": {"high":"这一层切开真漂亮，我舍不得马上吃。", "mid":"味道不错，摆得再整齐一点会更好看。", "low":"它在盒子里好像经历了一场地震。"},
    "阿栗": {"high":"这个搭配有意思，菜单上应该有它。", "mid":"挺稳的，不过还能再大胆一点。", "low":"今天的创意方向……有点迷路。"},
    "周姨": {"high":"做得仔细，什么都没落下。", "mid":"大体没错，再认真核对一次会更好。", "low":"孩子，订单上写的和这个不太一样。"},
    "沈昼": {"high":"这份够扎实，下午不会饿了。", "mid":"份量够了，其他细节再稳一点就更好了。", "low":"这份的份量或完成度还差一些。"},
    "诺亚": {"high":"层次很干净，吃起来也很舒服。", "mid":"搭配对了，摆放还能更利落。", "low":"我点的那份好像没有到这里。"},
    "蓁蓁": {"high":"完全是我想要的，谢谢你记得。", "mid":"已经很接近了，下次别漏掉细节。", "low":"这里面有我不吃的东西。"},
    "老曹": {"high":"这火候有准头。", "mid":"能吃，不过再早半分钟会更好。", "low":"烤台今天心情不好？"},
    "苏弥": {"high":"简单、准确，正合适。", "mid":"还行，酱料再稳一点。", "low":"我点的那份应该不是这个味道。"},
    "罗宾": {"high":"快，漂亮，我喜欢。", "mid":"速度还行，下次再利索一点。", "low":"我已经等得把招牌字数完了。"},
    "伊芙": {"high":"谢谢你认真对待素食要求。", "mid":"基本合格，不过细节还需要确认。", "low":"这份餐点触碰了我的饮食边界。"},
    "唐九": {"high":"不错。门后那张菜单，离你更近了一点。", "mid":"味道到了，答案还没到。", "low":"别急着问终点，先学会看懂订单。"},
}

ALIASES = {
    "bun":"原味胚","原味胚":"原味胚",
    "whole":"全麦胚","全麦胚":"全麦胚",
    "beef":"牛肉饼","牛肉饼":"牛肉饼",
    "chicken":"鸡肉饼","鸡肉饼":"鸡肉饼",
    "bacon":"培根","培根":"培根",
    "egg":"煎蛋","煎蛋":"煎蛋",
    "cheese":"芝士","芝士":"芝士",
    "lettuce":"生菜","生菜":"生菜",
    "tomato":"番茄","番茄":"番茄",
    "onion":"洋葱","洋葱":"洋葱",
    "pickle":"酸黄瓜","酸黄瓜":"酸黄瓜",
    "ketchup":"番茄酱","番茄酱":"番茄酱",
    "mayo":"蛋黄酱","蛋黄酱":"蛋黄酱",
    "chili":"辣酱","辣酱":"辣酱",
}
AMOUNTS = {
    "light":"少量","少量":"少量",
    "normal":"正常","正常":"正常",
    "heavy":"过量","过量":"过量",
}

INITIAL_STATE = {
    "version":"0.6",
    "shop_name":"",
    "chef_name":"",
    "sign_style":"",
    "day":1,
    "week":1,
    "coins":80,
    "reputation":0,
    "scores":[],
    "revenue":0,
    "tips":0,
    "daily_gross":0,
    "current_orders":[],
    "order_pointer":0,
    "current_order_accepted":False,
    "turn":0,
    "grill":{"1":None,"2":None},
    "cooked":[],
    "layers":[],
    "sauces":{},
    "customer_progress":{},
    "weekly_goal":"均衡经营",
    "renovations":{},
    "weekly_history":[],
    "journal":[],
    "tray":[],
    "custom_recipes":{},
    "last_build":[],
    "last_sauces":{},
}

def fresh_state():
    return json.loads(json.dumps(INITIAL_STATE, ensure_ascii=False))

def save(state):
    SAVE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

def load():
    if not SAVE_FILE.exists():
        return fresh_state()
    try:
        state = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fresh_state()
    for key, value in INITIAL_STATE.items():
        state.setdefault(key, json.loads(json.dumps(value, ensure_ascii=False)))
    state["version"] = "0.6"
    state.setdefault("tray", [])
    state.setdefault("custom_recipes", {})
    state.setdefault("last_build", [])
    state.setdefault("last_sauces", {})
    return state

def setup(state):
    if state["shop_name"]:
        return
    print("欢迎来到《午间汉堡铺》v0.6。")
    state["shop_name"] = input("请给店铺起名：\n> ").strip() or "无名汉堡铺"
    state["chef_name"] = input("请给主厨起名：\n> ").strip() or "无名主厨"
    print("招牌风格：1温馨 2复古 3极简 4怪诞")
    print("温馨：熟客关系成长更快｜复古：原创配方更容易正式上架")
    print("极简：完美摆放有奖励，但顾客耐心略低｜怪诞：创意与隐藏菜单收益更高")
    state["sign_style"] = {"1":"温馨","2":"复古","3":"极简","4":"怪诞"}.get(input("> ").strip(),"温馨")
    state["journal"].append(f"{state['shop_name']}开张，主厨{state['chef_name']}。")
    save(state)

def has_renovation(state, name):
    return bool(state.get("renovations", {}).get(name))

def unlocked(day):
    items = []
    for d in range(1, min(day,7)+1):
        items.extend(UNLOCKS.get(d,[]))
    return set(items)

def available_customers(day):
    pool = [c for c in CUSTOMERS if c["name"] != "唐九"]
    if day >= 7:
        pool.append(next(c for c in CUSTOMERS if c["name"] == "唐九"))
    return pool

def weekly_goal_bonus(state, category):
    mapping = {"速度优先":"speed","精致摆盘":"plating","顾客至上":"accuracy","利润冲刺":"profit"}
    return mapping.get(state.get("weekly_goal")) == category

def patience_bonus(state):
    return (1 if has_renovation(state,"窗边花架") else 0) + (2 if has_renovation(state,"舒适候餐区") else 0)

def grill_slots(state):
    return {"1":None,"2":None,"3":None} if has_renovation(state,"高级烤台") else {"1":None,"2":None}

def doneness(protein, t):
    if protein=="牛肉饼":
        return "生" if t<=1 else "嫩" if t==2 else "正好" if t==3 else "焦熟" if t==4 else "烧焦"
    if protein=="鸡肉饼":
        return "未熟" if t<=2 else "正好" if t==3 else "偏干" if t==4 else "烧焦"
    if protein=="煎蛋":
        return "流心" if t<=2 else "全熟" if t==3 else "焦"
    if protein=="培根":
        return "软" if t<=1 else "脆" if t==2 else "焦"
    return "未知"

def target_time(protein, target):
    table = {
        ("牛肉饼","嫩"):2, ("牛肉饼","正好"):3,
        ("鸡肉饼","正好"):3,
        ("煎蛋","流心"):2, ("煎蛋","全熟"):3,
        ("培根","软"):1, ("培根","脆"):2,
    }
    return table.get((protein,target))

def grill_hint(item, order=None):
    current = item["time"]
    now = doneness(item["protein"], current)
    target = None
    if order and order.get("protein") == item["protein"]:
        target = order.get("doneness")
    if target:
        tt = target_time(item["protein"], target)
        if tt is not None:
            delta = tt-current
            if delta>0:
                return f"当前{now}，再{delta}回合到“{target}”"
            if delta==0:
                return f"当前正是“{target}”，建议立即取出（take 不消耗回合）"
            return f"已超过“{target}”{abs(delta)}回合，建议立即取出"
    return f"当前熟度：{now}"

def varied_signature(order):
    return (
        order["customer"], order["bun"], order["protein"], order["doneness"],
        tuple(order["toppings"]), order["sauce"], order["sauce_amount"],
        order.get("vegetarian_rule"), order.get("batch_count",1)
    )

def generate_order(state, day, customer, force_batch=False):
    avail = unlocked(day)
    bun = random.choice(["原味胚"] + (["全麦胚"] if "全麦胚" in avail else []))
    vegetarian = customer["name"]=="伊芙"

    if vegetarian:
        protein = "煎蛋" if "煎蛋" in avail and random.random()<0.75 else None
    else:
        proteins = [p for p in ["牛肉饼","鸡肉饼"] if p in avail]
        liked = [p for p in proteins if p in customer["likes"]]
        protein = random.choice(liked or proteins)

    toppings_pool = [x for x in ["芝士","生菜","番茄","洋葱","酸黄瓜","培根"] if x in avail]
    toppings_pool = [x for x in toppings_pool if x not in customer["dislikes"]]
    if vegetarian:
        toppings_pool = [x for x in toppings_pool if x!="培根"]
        count = min(len(toppings_pool), random.randint(2,4))
    else:
        count = min(len(toppings_pool), random.randint(1,4))
    toppings = random.sample(toppings_pool,count) if count else []

    if customer["focus"]=="portion" and day>=5 and protein in ["牛肉饼","鸡肉饼"]:
        toppings.append(protein)

    sauces_pool = [x for x in ["番茄酱","蛋黄酱","辣酱"] if x in avail and x not in customer["dislikes"]]
    sauce = random.choice(sauces_pool) if sauces_pool and random.random()<0.72 else None
    sauce_amount = random.choice(["少量","正常"]) if sauce else None

    if protein=="牛肉饼":
        target = random.choice(["嫩","正好"])
    elif protein=="鸡肉饼":
        target = "正好"
    elif protein=="煎蛋":
        target = random.choice(["流心","全熟"])
    else:
        target = None

    lower = [x for x in toppings if x in ["生菜","番茄","洋葱","酸黄瓜"]]
    hot = [x for x in toppings if x in ["芝士","培根"]]
    protein_count = (1 + toppings.count(protein)) if protein else 0
    protein_layers = [protein] * protein_count if protein else []
    layers = [bun] + lower[:2] + protein_layers + hot + lower[2:] + [bun]

    vegetarian_rule = None
    if vegetarian:
        vegetarian_rule = random.choice([
            "蔬菜顺序必须完全正确",
            "不要添加任何肉类或多余酱料",
            "全麦与蔬菜搭配，摆放分要求更严格",
        ])
        if day>=2:
            bun = "全麦胚"
            layers[0] = layers[-1] = bun

    batch_count = 2 if force_batch else 1
    base_price = 12 + len(toppings)*2 + (5 if protein else 0) + (2 if sauce else 0)
    if toppings.count(protein)>0:
        base_price += 5
    if force_batch:
        base_price = int(base_price*1.75)

    cook_ops = 0 if not protein else target_time(protein,target) or 3
    # 放上烤台本身推进1回合；之后等待到目标时间。翻面不耗时。
    min_ops = cook_ops + 1 + (0 if has_renovation(state,"加宽操作台") else 1)
    if protein and layers.count(protein) > 1:
        min_ops += 1
    if sauce and not has_renovation(state,"自动酱料机"):
        min_ops += 1
    patience = min_ops + max(2, customer["patience"]-6) + patience_bonus(state)
    if force_batch:
        patience += 3
    if state.get("sign_style") == "极简":
        patience = max(2, patience - 1)

    return {
        "customer":customer["name"],
        "focus":customer["focus"],
        "patience":patience,
        "base_price":base_price + (2 if has_renovation(state,"霓虹招牌") else 0),
        "bun":bun,
        "protein":protein,
        "doneness":target,
        "toppings":toppings,
        "sauce":sauce,
        "sauce_amount":sauce_amount,
        "required_layers":layers,
        "dislikes":customer["dislikes"],
        "tip_mult":customer["tip"],
        "vegetarian":vegetarian,
        "vegetarian_rule":vegetarian_rule,
        "batch_count":batch_count,
    }

def generate_day(state):
    count = DAY_ORDER_COUNT.get(state["day"], min(10,8+(state["week"]-1)//2))
    customers = random.sample(available_customers(state["day"]), k=min(count,len(available_customers(state["day"]))))
    while len(customers)<count:
        customers.append(random.choice(available_customers(state["day"])))

    orders = []
    seen = set()
    for i, customer in enumerate(customers):
        force_batch = state["day"]>=5 and i==0
        for _ in range(30):
            order = generate_order(state,state["day"],customer,force_batch=force_batch)
            sig = varied_signature(order)
            # 前两天严格避免连续同型订单；后续也尽量避免重复。
            if sig not in seen:
                seen.add(sig)
                orders.append(order)
                break
        else:
            orders.append(order)

    random.shuffle(orders)
    if state["day"]>=5 and not any(o.get("batch_count",1)>1 for o in orders):
        orders[0] = generate_order(state,state["day"],random.choice(available_customers(state["day"])),force_batch=True)

    state["current_orders"]=orders
    state["order_pointer"]=0
    state["scores"]=[]
    state["revenue"]=0
    state["tips"]=0
    state["daily_gross"]=0
    reset_workspace(state)
    save(state)

def current_order(state):
    return state["current_orders"][state["order_pointer"]] if state["order_pointer"]<len(state["current_orders"]) else None

def reset_workspace(state):
    state["current_order_accepted"]=False
    state["turn"]=0
    state["grill"]=grill_slots(state)
    state["cooked"]=[]
    state["layers"]=[]
    state["sauces"]={}
    state["tray"]=[]
    state["last_build"]=[]
    state["last_sauces"]={}

def advance(state,steps=1):
    state["turn"] += steps
    for item in state["grill"].values():
        if item:
            item["time"] += steps

def resolve_food(token):
    return ALIASES.get(token.lower(), ALIASES.get(token))

def grill_item(state, token):
    p = resolve_food(token)
    if p not in ["牛肉饼","鸡肉饼","煎蛋","培根"]:
        print("可烹饪：beef/牛肉饼、chicken/鸡肉饼、egg/煎蛋、bacon/培根")
        return
    slot = next((k for k,v in state["grill"].items() if v is None),None)
    if not slot:
        print("烤台已满。")
        return
    state["grill"][slot]={"protein":p,"time":0,"flipped":False}
    advance(state)
    print(f"{p}已放上{slot}号烤位。")
    print(grill_hint(state["grill"][slot],current_order(state)))

def flip(state,slot):
    item = state["grill"].get(slot)
    if not item:
        print("这个烤位为空。")
        return
    if item["flipped"]:
        print("已经翻过面。")
        return
    item["flipped"]=True
    # v0.5：翻面不推进时间，避免“翻面陷阱”
    print(f"{slot}号烤位已翻面。本次翻面不消耗回合。")
    print(grill_hint(item,current_order(state)))

def wait_turn(state):
    advance(state)
    print("等待1回合。")
    show_grill(state)

def take(state,slot):
    item = state["grill"].get(slot)
    if not item:
        print("这个烤位为空。")
        return
    item["doneness"]=doneness(item["protein"],item["time"])
    state["cooked"].append(item)
    state["grill"][slot]=None
    print(f"取出{item['protein']}，熟度：{item['doneness']}。本次 take 不消耗回合，取出后不会继续加热。")

def build(state,tokens):
    layers=[]
    for token in tokens:
        food = resolve_food(token)
        if not food:
            print(f"无法识别食材：{token}")
            print("可直接使用中文，或输入 help 查看中英对照。")
            return
        layers.append(food)
    state["last_build"]=list(state.get("layers", []))
    state["last_sauces"]=dict(state.get("sauces", {}))
    state["layers"]=layers
    if not has_renovation(state,"加宽操作台"):
        advance(state)
    print("已组装："," → ".join(layers))

def add_sauce(state,token,amount):
    sauce = resolve_food(token)
    amount_cn = AMOUNTS.get(amount.lower(),AMOUNTS.get(amount))
    if sauce not in ["番茄酱","蛋黄酱","辣酱"]:
        print("酱料支持：ketchup/番茄酱、mayo/蛋黄酱、chili/辣酱")
        return
    if not amount_cn:
        print("用量支持：light/少量、normal/正常、heavy/过量")
        return
    state["last_sauces"]=dict(state.get("sauces", {}))
    state["sauces"][sauce]=amount_cn
    if not has_renovation(state,"自动酱料机"):
        advance(state)
    print(f"已加入{sauce}：{amount_cn}。")

def _workspace_snapshot(state, consume=False):
    layers=list(state.get("layers", []))
    sauces=dict(state.get("sauces", {}))
    grillables={"牛肉饼","鸡肉饼","煎蛋","培根"}
    needed=Counter(x for x in layers if x in grillables)
    selected=[]
    keep=[]
    for item in state.get("cooked", []):
        protein=item.get("protein")
        if needed.get(protein,0)>0:
            selected.append(dict(item))
            needed[protein]-=1
        else:
            keep.append(item)
    if consume:
        state["cooked"]=keep
    return {"layers":layers,"sauces":sauces,"cooked":selected}

def plate_current(state):
    o=current_order(state)
    if not o:
        print("当前没有订单。")
        return
    if not state.get("layers"):
        print("当前还没有组装汉堡，先使用 build。")
        return
    needed=o.get("batch_count",1)
    if len(state.get("tray",[]))>=needed:
        print(f"托盘已经有足够的{needed}份汉堡。")
        return
    snap=_workspace_snapshot(state, consume=True)
    state.setdefault("tray", []).append(snap)
    idx=len(state["tray"])
    state["layers"]=[]
    state["sauces"]={}
    print(f"第{idx}份汉堡已放上托盘。托盘进度：{idx}/{o.get('batch_count',1)}。")

def show_tray(state):
    tray=state.get("tray",[])
    if not tray:
        print("托盘目前是空的。")
        return
    print("\n=== 托盘 ===")
    for i,item in enumerate(tray,1):
        sauce_text="、".join(f"{k}:{v}" for k,v in item.get("sauces",{}).items()) or "无"
        print(f"{i}. {' → '.join(item.get('layers',[]))}｜酱料：{sauce_text}")

def evaluate(state,o,work=None):
    details=[]
    work=work or _workspace_snapshot(state, consume=False)
    layers=list(work.get("layers", []))
    sauces=dict(work.get("sauces", {}))
    cooked=list(work.get("cooked", []))
    accuracy,fire,plating,speed=40,25,15,20
    actual=Counter(layers); expected=Counter(o["required_layers"])
    missing=list((expected-actual).elements())
    extra=list((actual-expected).elements())

    if missing:
        p=min(24,6*len(missing)); accuracy-=p; details.append(f"缺少{'、'.join(missing)} -{p}")
    if extra:
        p=min(20,5*len(extra)); accuracy-=p; details.append(f"多余{'、'.join(extra)} -{p}")

    portion_diff=sum(abs(actual[k]-expected[k]) for k in set(actual)|set(expected))
    if portion_diff==0:
        portion_note="份量与食材数量完全符合订单"
    else:
        portion_note=f"份量存在{portion_diff}处数量偏差"
    if o["focus"]=="portion" and portion_diff>0:
        extra_penalty=min(8,2*portion_diff)
        accuracy-=extra_penalty
        details.append(f"此顾客格外在意份量，数量偏差额外 -{extra_penalty}")

    for bad in o["dislikes"]:
        if bad in layers or bad in sauces:
            accuracy-=15; details.append(f"触发忌口：{bad} -15")

    if o["sauce"]:
        got=sauces.get(o["sauce"])
        if got is None:
            accuracy-=8; details.append(f"缺少{o['sauce']} -8")
        elif got!=o["sauce_amount"]:
            accuracy-=5; details.append(f"{o['sauce']}用量错误 -5")
        for sauce_name in sauces:
            if sauce_name!=o["sauce"]:
                accuracy-=6; details.append(f"多加酱料{sauce_name} -6")
    elif sauces:
        accuracy-=10; details.append("本单不要酱 -10")

    if o["protein"]:
        matching_cooked=[x for x in cooked if x["protein"]==o["protein"]]
        required_count=o["required_layers"].count(o["protein"])
        cooked_item=matching_cooked[0] if matching_cooked else None
        if len(matching_cooked)<required_count:
            fire=max(0,fire-12*(required_count-len(matching_cooked)))
            details.append(f"主食材数量不足：需要{required_count}份，完成{len(matching_cooked)}份")
        if not cooked_item:
            fire=0; details.append("主食材未完成 -25")
        else:
            wrong=[x for x in matching_cooked if x["doneness"]!=o["doneness"]]
            if wrong:
                fire=max(0,fire-12); details.append(f"目标{o['doneness']}，有{len(wrong)}份火候不符 -12")
            unflipped=[x for x in matching_cooked if o["protein"] in ["牛肉饼","鸡肉饼"] and not x["flipped"]]
            if unflipped:
                fire=min(fire,15); details.append("存在未翻面主食材：火候分上限15/25")
    elif o["vegetarian"]:
        if extra:
            accuracy-=4
            details.append("素食单额外食材处罚 -4")
        if layers!=o["required_layers"]:
            plating=max(0,plating-3)
            details.append("素食单要求严格摆放 -3")

    if layers!=o["required_layers"]:
        common=sum(1 for i,x in enumerate(layers) if i<len(o["required_layers"]) and x==o["required_layers"][i])
        plating=min(plating,int(15*common/max(1,len(o["required_layers"]))))
        details.append(f"层次顺序部分正确 {plating}/15")
    elif state.get("sign_style")=="极简":
        plating=min(15,plating+2)
        details.append("极简招牌：完美摆放奖励 +2")

    patience_left=o["patience"]-state["turn"]
    if patience_left>=2: speed=20
    elif patience_left==1: speed=17
    elif patience_left==0: speed=13
    else:
        speed=max(0,13+patience_left*3)
        details.append(f"出餐延迟，速度{speed}/20")

    focus_extra=None
    if o["focus"]=="speed" and speed<20:
        speed=max(0,speed-2); focus_extra="速度偏差额外 -2"; details.append("顾客特别在意速度 -2")
    if o["focus"]=="plating" and plating<15:
        plating=max(0,plating-2); focus_extra="摆放偏差额外 -2"; details.append("顾客特别在意摆放 -2")
    if o["focus"]=="fire" and fire<25:
        fire=max(0,fire-3); focus_extra="火候偏差额外 -3"; details.append("顾客特别在意火候 -3")
    if o["focus"]=="accuracy" and accuracy<40:
        accuracy=max(0,accuracy-2); focus_extra="准确度偏差额外 -2"; details.append("顾客特别在意准确度 -2")
    if o["focus"]=="portion" and portion_diff>0:
        focus_extra="份量偏差会追加扣分"

    if has_renovation(state,"招牌照片墙"):
        plating=max(plating,8)
    if weekly_goal_bonus(state,"speed"): speed=min(20,speed+2)
    if weekly_goal_bonus(state,"plating"): plating=min(15,plating+2)
    if weekly_goal_bonus(state,"accuracy"): accuracy=min(40,accuracy+2)

    accuracy=max(0,min(40,accuracy))
    fire=max(0,min(25,fire))
    plating=max(0,min(15,plating))
    speed=max(0,min(20,speed))
    total=max(0,min(100,accuracy+fire+plating+speed))
    return {"accuracy":accuracy,"fire":fire,"plating":plating,"speed":speed,
            "total":total,"details":details,"portion_note":portion_note,
            "focus_extra":focus_extra}

def show_order(state):
    o=current_order(state)
    if not o:
        print("今天没有订单。")
        return
    print(f"\n【第{state['order_pointer']+1}单｜{o['customer']}】")
    if o.get("batch_count",1)>1:
        print(f"【真实批量订单】需要完成{o['batch_count']}份汉堡；每份完成后使用 plate 放上托盘。")
    print("从下到上："," → ".join(o["required_layers"]))
    print("主食材：",o["protein"] or "无肉素食")
    print("目标熟度：",o["doneness"] or "无需烤台")
    print("酱料：",f"{o['sauce']}（{o['sauce_amount']}）" if o["sauce"] else "不要酱")
    print("耐心：",o["patience"],"回合")
    label=FOCUS_LABELS.get(o["focus"],o["focus"])
    print("顾客重点：",label)
    print(f"提示：此顾客更在意{label}，相关偏差会产生额外影响。")
    if o.get("vegetarian_rule"):
        print("素食要求：",o["vegetarian_rule"])

def show_grill(state):
    o=current_order(state)
    print("\n=== 烤台状态 ===")
    for slot,item in state["grill"].items():
        if not item:
            print(f"{slot}号：空")
        else:
            flip_text="已翻面" if item["flipped"] else "未翻面"
            print(f"{slot}号：{item['protein']}｜{flip_text}｜{grill_hint(item,o)}")

def status(state):
    print(f"\n{state['shop_name']}｜主厨{state['chef_name']}")
    print(f"第{state['day']}天｜第{state['week']}周")
    print(f"当前总金币：{state['coins']}｜今日累计收入：{state.get('daily_gross',0)}｜声誉：{state['reputation']}")
    print("本周目标：",state.get("weekly_goal","均衡经营"))
    style=state.get("sign_style","温馨")
    print(f"招牌风格：{style}｜{SIGN_STYLE_EFFECTS.get(style,'暂无额外效果')}")
    print("装修：","、".join(k for k,v in state.get("renovations",{}).items() if v) or "暂无")
    print(f"当前订单：{state['order_pointer']+1}/{len(state['current_orders'])}｜本单已用回合：{state['turn']}")
    show_grill(state)
    print("已取出：",state["cooked"] or "无")
    print("组装："," → ".join(state["layers"]) or "未开始")
    print("酱料：",state["sauces"] or "无")
    print(f"托盘：{len(state.get('tray',[]))}份")
    official=sum(1 for r in state.get("custom_recipes",{}).values() if r.get("official"))
    print(f"原创配方：{len(state.get('custom_recipes',{}))}个｜正式上架：{official}个")

def check_order(state):
    o=current_order(state)
    if not o:
        print("当前没有订单。")
        return
    print("\n=== 出餐前检查 ===")
    count=o.get("batch_count",1)
    print("托盘进度：",f"{len(state.get('tray',[]))}/{count}")
    works=[]
    if state.get("tray"):
        works.extend(state["tray"][:count])
    if state.get("layers"):
        works.append(_workspace_snapshot(state, consume=False))
    if not works:
        print("还没有组装中的汉堡，也没有已完成的托盘餐点。")
        print("check 只提供检查，不会自动修改，也不消耗回合。")
        return
    for idx,work in enumerate(works,1):
        actual=Counter(work["layers"]); expected=Counter(o["required_layers"])
        missing=list((expected-actual).elements())
        extra=list((actual-expected).elements())
        label=f"第{idx}份" if count>1 else "当前汉堡"
        print(f"[{label}] 缺少：{'、'.join(missing) if missing else '无'}")
        print(f"[{label}] 多余：{'、'.join(extra) if extra else '无'}")
        if o["protein"]:
            matching=[x for x in work["cooked"] if x["protein"]==o["protein"]]
            needed=o["required_layers"].count(o["protein"])
            if matching:
                states="、".join(x.get("doneness","未知") for x in matching)
                print(f"[{label}] 主食材：{len(matching)}/{needed}份，实际熟度{states}，目标{o['doneness']}")
            else:
                print(f"[{label}] 主食材：0/{needed}份，尚未放入或尚未取出")
        expected_sauce=f"{o['sauce']}（{o['sauce_amount']}）" if o["sauce"] else "不要酱"
        print(f"[{label}] 目标酱料：{expected_sauce}｜当前：{work['sauces'] or '无'}")
    if count>1 and len(state.get("tray",[]))<count:
        print(f"批量订单仍需完成{count-len(state.get('tray',[]))}份并使用 plate 放上托盘。")
    print("check 只提供检查，不会自动修改，也不消耗回合。")

def undo_build(state):
    if not state.get("layers"):
        print("当前没有可撤销的组装。")
        return
    state["layers"]=list(state.get("last_build",[]))
    print("已撤销最近一次 build。已消耗的回合不会返还。")

def clear_sauce(state):
    if not state.get("sauces"):
        print("当前没有酱料。")
        return
    state["sauces"]={}
    print("已清除当前汉堡上的全部酱料。此前消耗的回合不会返还。")

def discard_slot(state,slot):
    if slot in state.get("grill",{}) and state["grill"][slot]:
        item=state["grill"][slot]
        state["grill"][slot]=None
        print(f"已丢弃{slot}号烤位上的{item['protein']}。")
        return
    print("该烤位为空，无法丢弃。")

def customer_profile(state,name):
    customer=next((c for c in CUSTOMERS if c["name"]==name),None)
    if not customer:
        print("没有找到这位顾客。可输入完整姓名。")
        return
    label=FOCUS_LABELS.get(customer["focus"],customer["focus"])
    progress=state.get("customer_progress",{}).get(name,0)
    stage="初识" if progress<2 else "熟悉" if progress<5 else "熟客" if progress<8 else "信赖"
    print(f"\n=== 顾客档案：{name} ===")
    print(f"关系：{stage}（{progress}）｜重点：{label}｜基础耐心：{customer['patience']}")
    print("喜欢：","、".join(customer["likes"]) or "暂无明确偏好")
    print("不喜欢：","、".join(customer["dislikes"]) or "暂无明确忌口")

def show_history(state):
    entries=state.get("journal",[])[-10:]
    if not entries:
        print("还没有营业记录。")
        return
    print("\n=== 最近记录 ===")
    for line in entries:
        print("-",line)

def _recipe_feedback_score(state,recipe,customer):
    ingredients=set(recipe.get("layers",[])) | set(recipe.get("sauces",{}))
    score=sum(1 for x in customer["likes"] if x in ingredients)
    score-=sum(2 for x in customer["dislikes"] if x in ingredients)
    if customer["focus"]=="innovation": score+=1
    if state.get("sign_style")=="怪诞": score+=1
    if customer["name"]=="伊芙" and any(x in ingredients for x in ["牛肉饼","鸡肉饼","培根"]):
        score-=5
    return score

def create_recipe(state,name):
    if state.get("day",1)<6:
        print("隐藏菜单将在第6天开放。")
        return
    if not state.get("layers"):
        print("请先 build 组装一份样品，再使用 create 配方名。")
        return
    if name in state.setdefault("custom_recipes",{}):
        print("已经存在同名配方。")
        return
    state["custom_recipes"][name]={
        "layers":list(state["layers"]),
        "sauces":dict(state.get("sauces",{})),
        "testers":[],"feedback":[],"official":False
    }
    print(f"已记录原创配方“{name}”。使用 test {name} 邀请当前顾客试吃。")

def test_recipe(state,name):
    recipe=state.get("custom_recipes",{}).get(name)
    if not recipe:
        print("没有找到这个原创配方。")
        return
    o=current_order(state)
    if not o:
        print("当前没有可邀请试吃的顾客。")
        return
    customer=next(c for c in CUSTOMERS if c["name"]==o["customer"])
    if customer["name"] in recipe["testers"]:
        print(f"{customer['name']}已经试吃过这份配方。")
        return
    score=_recipe_feedback_score(state,recipe,customer)
    recipe["testers"].append(customer["name"])
    recipe["feedback"].append(score)
    if score>=3:
        text="非常喜欢，觉得它有资格写进正式菜单"
    elif score>=1:
        text="愿意再吃一次，但还可以继续调整"
    else:
        text="觉得这份搭配暂时不适合自己"
    print(f"{customer['name']}试吃后{text}。试吃评价：{score:+d}")
    need=2 if state.get("sign_style")=="复古" else 3
    avg=sum(recipe["feedback"])/len(recipe["feedback"])
    if len(recipe["testers"])>=need and avg>=1 and not recipe["official"]:
        recipe["official"]=True
        print(f"原创配方“{name}”正式进入隐藏菜单！匹配该配方出餐时会获得额外收入。")
    else:
        print(f"正式上架进度：{len(recipe['testers'])}/{need}位不同顾客，当前平均评价{avg:.1f}。")

def show_recipes(state):
    recipes=state.get("custom_recipes",{})
    if not recipes:
        print("还没有原创配方。第6天后可先组装样品，再输入 create 配方名。")
        return
    print("\n=== 原创配方 ===")
    for name,r in recipes.items():
        status_text="正式上架" if r.get("official") else "试吃中"
        print(f"- {name}｜{status_text}｜试吃{len(r.get('testers',[]))}人｜{' → '.join(r.get('layers',[]))}")

def matching_official_recipe(state,work):
    for name,r in state.get("custom_recipes",{}).items():
        if r.get("official") and r.get("layers")==work.get("layers") and r.get("sauces",{})==work.get("sauces",{}):
            return name
    return None

def customer_reaction(name,total):
    group="high" if total>=90 else "mid" if total>=60 else "low"
    return CUSTOMER_REACTIONS.get(name,{}).get(group,"谢谢。")

def cheapest_affordable(state):
    options=[(name,info) for name,info in RENOVATIONS.items()
             if not has_renovation(state,name) and state["coins"]>=info["cost"]]
    return min(options,key=lambda x:x[1]["cost"]) if options else None

def renovation_reminder(state):
    item=cheapest_affordable(state)
    if item:
        name,info=item
        print(f"【装修提醒】当前金币足够购买“{name}”（{info['cost']}金币）：{info['desc']}")
        print("输入 renovate 可打开装修商店。")
    else:
        remaining=[info["cost"] for name,info in RENOVATIONS.items() if not has_renovation(state,name)]
        if remaining:
            need=max(0,min(remaining)-state["coins"])
            print(f"【装修提醒】再攒{need}金币即可购买最便宜的下一项装修。")

def serve(state):
    o=current_order(state)
    if not o:
        print("今天没有订单。"); return
    if not state["current_order_accepted"]:
        print("请先 accept 接单。"); return

    count=o.get("batch_count",1)
    if count>1:
        if state.get("layers"):
            print("当前还有一份汉堡未放上托盘，请先使用 plate。")
            return
        if len(state.get("tray",[]))<count:
            print(f"批量订单尚未完成：托盘需要{count}份，当前{len(state.get('tray',[]))}份。")
            return
        works=state["tray"][:count]
    else:
        if state.get("tray"):
            works=[state["tray"][0]]
        else:
            if not state.get("layers"):
                print("当前还没有组装汉堡。")
                return
            works=[_workspace_snapshot(state, consume=False)]

    results=[evaluate(state,o,work) for work in works]
    avg_total=round(sum(r["total"] for r in results)/len(results))
    avg_accuracy=round(sum(r["accuracy"] for r in results)/len(results))
    avg_fire=round(sum(r["fire"] for r in results)/len(results))
    avg_plating=round(sum(r["plating"] for r in results)/len(results))
    avg_speed=round(sum(r["speed"] for r in results)/len(results))

    paid=o["base_price"] if avg_total>=40 else 0
    tip=0
    if avg_total>=90: tip=int(o["base_price"]*0.30*o["tip_mult"])
    elif avg_total>=75: tip=int(o["base_price"]*0.10*o["tip_mult"])
    profit_bonus=2 if weekly_goal_bonus(state,"profit") else 0

    matched=[matching_official_recipe(state,w) for w in works]
    matched=[x for x in matched if x]
    recipe_bonus=0
    if matched:
        per=3 if state.get("sign_style")=="复古" else 2
        if state.get("sign_style")=="怪诞": per+=1
        recipe_bonus=per*len(matched)

    earned=paid+tip+profit_bonus+recipe_bonus
    state["scores"].append(avg_total)
    state["revenue"]+=paid
    state["tips"]+=tip
    state["coins"]+=earned
    state["daily_gross"]+=earned

    print("\n=== 出餐评分 ===")
    print(f"顾客重点：{FOCUS_LABELS.get(o['focus'],o['focus'])}")
    print(f"准确度 {avg_accuracy}/40")
    print(f"火候 {avg_fire}/25")
    print(f"摆放 {avg_plating}/15")
    print(f"速度 {avg_speed}/20")
    print(f"总分 {avg_total}/100")
    if count>1:
        print(f"批量订单共{count}份，最终成绩取各份平均。")
    for idx,r in enumerate(results,1):
        prefix=f"第{idx}份：" if count>1 else ""
        print(f"{prefix}{r['portion_note']}")
        if r.get("focus_extra"):
            print(f"{prefix}专精影响：{r['focus_extra']}")
        for detail in r["details"]:
            print(f"- {prefix}{detail}")
    if matched:
        print(f"隐藏菜单命中：{'、'.join(matched)}，原创配方奖励 +{recipe_bonus}")
    print(f"{o['customer']}：“{customer_reaction(o['customer'],avg_total)}”")
    print(f"本单收入：{paid}｜小费：{tip}｜目标奖励：{profit_bonus}｜配方奖励：{recipe_bonus}")
    print(f"当前总金币：{state['coins']}")
    print(f"今日累计收入：{state['daily_gross']}")

    if avg_total>=75:
        gain=2 if state.get("sign_style")=="温馨" else 1
        state["customer_progress"][o["customer"]]=state["customer_progress"].get(o["customer"],0)+gain
        if gain>1:
            print("温馨招牌使熟客关系额外成长。")
    state["journal"].append(f"第{state['day']}天第{state['order_pointer']+1}单：{o['customer']}，{avg_total}分。")
    state["order_pointer"]+=1
    reset_workspace(state)
    if state["order_pointer"]>=len(state["current_orders"]):
        finish_day(state)
    else:
        renovation_reminder(state)
    save(state)

def renovation_shop(state):
    while True:
        print("\n=== 店铺装修 ===")
        print("当前总金币：",state["coins"])
        items=list(RENOVATIONS.items())
        for i,(name,info) in enumerate(items,1):
            owned="【已拥有】" if has_renovation(state,name) else f"{info['cost']}金币"
            afford="" if has_renovation(state,name) or state["coins"]>=info["cost"] else "【金币不足】"
            print(f"{i}. {name} - {owned} {afford} - {info['desc']}")
        print("0. 离开装修店")
        raw=input("> ").strip()
        if raw=="0": break
        if not raw.isdigit() or not 1<=int(raw)<=len(items):
            print("无效选择。"); continue
        name,info=items[int(raw)-1]
        if has_renovation(state,name):
            print("已经拥有这项装修。"); continue
        if state["coins"]<info["cost"]:
            print(f"金币不足，还差{info['cost']-state['coins']}。"); continue
        state["coins"]-=info["cost"]
        state["renovations"][name]=True
        print(f"已购买：{name}。{info['desc']}")
        print("剩余金币：",state["coins"])
        save(state)

def choose_weekly_goal(state):
    goals=["均衡经营","速度优先","精致摆盘","顾客至上","利润冲刺"]
    print("\n请选择下一周经营目标：")
    for i,g in enumerate(goals,1): print(f"{i}. {g}")
    raw=input("> ").strip()
    state["weekly_goal"]=goals[int(raw)-1] if raw.isdigit() and 1<=int(raw)<=len(goals) else "均衡经营"
    print("下一周目标：",state["weekly_goal"])

def finish_day(state):
    avg=round(sum(state["scores"])/len(state["scores"]),1)
    fixed=23+max(0,state["week"]-1)*2
    state["coins"]-=fixed
    bonus=20 if avg>=90 else 10 if avg>=75 else 0
    rep=8 if avg>=90 else 5 if avg>=75 else 2 if avg>=60 else -3
    if has_renovation(state,"暖色吊灯"): rep+=1
    state["coins"]+=bonus
    state["reputation"]+=rep

    print("\n====================")
    print(f"第{state['day']}天结算")
    print("====================")
    print("营业额：",state["revenue"])
    print("小费：",state["tips"])
    print("今日累计收入：",state["daily_gross"])
    print(f"固定成本：-{fixed}")
    print("结算奖励：",bonus)
    print("平均分：",avg)
    print("当前总金币：",state["coins"])
    print("声誉：",state["reputation"])
    renovation_reminder(state)

    if state["day"]%7==0:
        rating="S" if avg>=92 and state["coins"]>=250 else "A" if avg>=85 else "B" if avg>=75 else "C" if avg>=60 else "D"
        state["weekly_history"].append({"week":state["week"],"rating":rating,"coins":state["coins"],"reputation":state["reputation"]})
        print(f"\n第{state['week']}周完成！评级：{rating}")
        print("周结算完成，现在自动进入装修环节。")
        renovation_shop(state)
        choose_weekly_goal(state)
        state["week"]+=1

    state["day"]+=1
    generate_day(state)
    print(f"\n进入第{state['day']}天。")
    if state["day"]<=7:
        print("今日解锁：","、".join(UNLOCKS.get(state["day"],[])) or "无新增")
    show_order(state)
    save(state)

HELP = """
常用指令：
status                         查看金币、招牌效果、烤台与托盘
orders                         查看当前订单与顾客专精提示
accept                         接单
grill beef                     放上牛肉饼
flip 1                         翻1号烤位；不消耗回合
wait                           等待1回合
take 1                         取出食材；不消耗回合且停止加热
build bun lettuce beef bun     组装当前这一份汉堡
sauce ketchup light            添加酱料
check                          出餐前检查缺漏、火候和酱料
plate                          把当前汉堡放上托盘（批量订单使用）
tray                           查看托盘
serve                          出餐

补救与档案：
undo build                     撤销最近一次组装，已耗回合不返还
clear sauce                    清除当前汉堡全部酱料
discard 1                      丢弃指定烤位食材
customer 伊芙                  查看顾客档案与关系
history                        查看最近10条营业记录

隐藏菜单（第6天开放）：
create 月光汉堡                将当前组装记录为原创配方
test 月光汉堡                  邀请当前顾客试吃
recipes                        查看原创配方和上架进度

其它：
renovate                       打开装修商店
save                           保存
quit                           保存并退出

中英对照：
bun=原味胚  whole=全麦胚
beef=牛肉饼  chicken=鸡肉饼  egg=煎蛋  bacon=培根
cheese=芝士  lettuce=生菜  tomato=番茄
onion=洋葱  pickle=酸黄瓜
ketchup=番茄酱  mayo=蛋黄酱  chili=辣酱
light=少量  normal=正常  heavy=过量

火候提示：
达到目标熟度时会明确提示立即 take；take 与 flip 都不推进时间。
等待、放上烤台、普通组装和普通加酱会推进时间。
"""

def main():
    state=load()
    setup(state)
    if not state["current_orders"]:
        generate_day(state)
    print(f"\n欢迎回到「{state['shop_name']}」。")
    show_order(state)
    print(HELP)
    while True:
        raw=input("\n> ").strip()
        if not raw: continue
        parts=raw.split()
        cmd=parts[0].lower()
        if cmd=="status": status(state)
        elif cmd=="orders": show_order(state)
        elif cmd=="accept":
            state["current_order_accepted"]=True
            print("已接单。")
        elif cmd=="grill" and len(parts)==2: grill_item(state,parts[1])
        elif cmd=="flip" and len(parts)==2: flip(state,parts[1])
        elif cmd=="wait": wait_turn(state)
        elif cmd=="take" and len(parts)==2: take(state,parts[1])
        elif cmd=="build" and len(parts)>1: build(state,parts[1:])
        elif cmd=="sauce" and len(parts)==3: add_sauce(state,parts[1],parts[2])
        elif cmd=="check": check_order(state)
        elif cmd=="plate": plate_current(state)
        elif cmd=="tray": show_tray(state)
        elif cmd=="undo" and len(parts)==2 and parts[1].lower()=="build": undo_build(state)
        elif cmd=="clear" and len(parts)==2 and parts[1].lower()=="sauce": clear_sauce(state)
        elif cmd=="discard" and len(parts)==2: discard_slot(state,parts[1])
        elif cmd=="customer" and len(parts)>=2: customer_profile(state," ".join(parts[1:]))
        elif cmd=="history": show_history(state)
        elif cmd=="create" and len(parts)>=2: create_recipe(state," ".join(parts[1:]))
        elif cmd=="test" and len(parts)>=2: test_recipe(state," ".join(parts[1:]))
        elif cmd=="recipes": show_recipes(state)
        elif cmd=="serve":
            serve(state)
            if state["order_pointer"]<len(state["current_orders"]): show_order(state)
        elif cmd=="renovate": renovation_shop(state)
        elif cmd=="save": save(state); print("已保存。")
        elif cmd=="help": print(HELP)
        elif cmd=="quit": save(state); print("已保存并退出。"); break
        else: print("无法识别。输入 help 查看完整指令。")
        save(state)

if __name__=="__main__":
    main()
