#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
《午间汉堡铺》v0.5
AI 玩家经营汉堡店：
- 12 位顾客
- 随机订单与前期防重复
- 清晰火候倒计时
- 翻面不再推进时间
- 中英文食材指令
- 第 5 天保证出现批量订单
- 总金币、今日累计收入、装修提醒
- 无限周目与本地存档
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
    "version":"0.5",
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
    state["version"] = "0.5"
    return state

def setup(state):
    if state["shop_name"]:
        return
    print("欢迎来到《午间汉堡铺》v0.5。")
    state["shop_name"] = input("请给店铺起名：\n> ").strip() or "无名汉堡铺"
    state["chef_name"] = input("请给主厨起名：\n> ").strip() or "无名主厨"
    print("招牌风格：1温馨 2复古 3极简 4怪诞")
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
                return f"当前正是“{target}”，建议立即取出"
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
    layers = [bun] + lower[:2] + ([protein] if protein else []) + hot + lower[2:] + [bun]

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
    if sauce and not has_renovation(state,"自动酱料机"):
        min_ops += 1
    patience = min_ops + max(2, customer["patience"]-6) + patience_bonus(state)
    if force_batch:
        patience += 3

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
    print(f"取出{item['protein']}，熟度：{item['doneness']}。")

def build(state,tokens):
    layers=[]
    for token in tokens:
        food = resolve_food(token)
        if not food:
            print(f"无法识别食材：{token}")
            print("可直接使用中文，或输入 help 查看中英对照。")
            return
        layers.append(food)
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
    state["sauces"][sauce]=amount_cn
    if not has_renovation(state,"自动酱料机"):
        advance(state)
    print(f"已加入{sauce}：{amount_cn}。")

def evaluate(state,o):
    details=[]
    accuracy,fire,plating,speed=40,25,15,20
    actual=Counter(state["layers"]); expected=Counter(o["required_layers"])
    missing=list((expected-actual).elements())
    extra=list((actual-expected).elements())

    if missing:
        p=min(24,6*len(missing)); accuracy-=p; details.append(f"缺少{'、'.join(missing)} -{p}")
    if extra:
        p=min(20,5*len(extra)); accuracy-=p; details.append(f"多余{'、'.join(extra)} -{p}")

    for bad in o["dislikes"]:
        if bad in state["layers"] or bad in state["sauces"]:
            accuracy-=15; details.append(f"触发忌口：{bad} -15")

    if o["sauce"]:
        got=state["sauces"].get(o["sauce"])
        if got is None:
            accuracy-=8; details.append(f"缺少{o['sauce']} -8")
        elif got!=o["sauce_amount"]:
            accuracy-=5; details.append(f"{o['sauce']}用量错误 -5")
        for s in state["sauces"]:
            if s!=o["sauce"]:
                accuracy-=6; details.append(f"多加酱料{s} -6")
    elif state["sauces"]:
        accuracy-=10; details.append("本单不要酱 -10")

    if o["protein"]:
        cooked = next((x for x in state["cooked"] if x["protein"]==o["protein"]),None)
        if not cooked:
            fire=0; details.append("主食材未完成 -25")
        else:
            if cooked["doneness"]!=o["doneness"]:
                fire-=12; details.append(f"目标{o['doneness']}，实际{cooked['doneness']} -12")
            if o["protein"] in ["牛肉饼","鸡肉饼"] and not cooked["flipped"]:
                fire=min(fire,15); details.append("未翻面：火候分上限15/25")
    else:
        # 素食单不再白送满分：摆放与多余食材更严格。
        if o["vegetarian"]:
            if extra:
                accuracy-=4
                details.append("素食单额外食材处罚 -4")
            if state["layers"]!=o["required_layers"]:
                plating=max(0,plating-3)
                details.append("素食单要求严格摆放 -3")

    if state["layers"]!=o["required_layers"]:
        common=sum(1 for i,x in enumerate(state["layers"]) if i<len(o["required_layers"]) and x==o["required_layers"][i])
        plating=min(plating,int(15*common/max(1,len(o["required_layers"]))))
        details.append(f"层次顺序部分正确 {plating}/15")

    patience_left=o["patience"]-state["turn"]
    if patience_left>=2: speed=20
    elif patience_left==1: speed=17
    elif patience_left==0: speed=13
    else:
        speed=max(0,13+patience_left*3)
        details.append(f"出餐延迟，速度{speed}/20")

    if o["focus"]=="speed" and speed<20:
        speed=max(0,speed-2); details.append("顾客特别在意速度 -2")
    if o["focus"]=="plating" and plating<15:
        plating=max(0,plating-2); details.append("顾客特别在意摆放 -2")
    if o["focus"]=="fire" and fire<25:
        fire=max(0,fire-3); details.append("顾客特别在意火候 -3")
    if o["focus"]=="accuracy" and accuracy<40:
        accuracy=max(0,accuracy-2); details.append("顾客特别在意准确度 -2")

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

    paid=o["base_price"] if total>=40 else 0
    tip=0
    if total>=90: tip=int(o["base_price"]*0.30*o["tip_mult"])
    elif total>=75: tip=int(o["base_price"]*0.10*o["tip_mult"])

    return {"accuracy":accuracy,"fire":fire,"plating":plating,"speed":speed,
            "total":total,"paid":paid,"tip":tip,"details":details}

def show_order(state):
    o=current_order(state)
    if not o:
        print("今天没有订单。")
        return
    print(f"\n【第{state['order_pointer']+1}单｜{o['customer']}】")
    if o.get("batch_count",1)>1:
        print(f"【批量订单】需要同时完成{o['batch_count']}份，已增加耐心与收入。")
    print("从下到上："," → ".join(o["required_layers"]))
    print("主食材：",o["protein"] or "无肉素食")
    print("目标熟度：",o["doneness"] or "无需烤台")
    print("酱料：",f"{o['sauce']}（{o['sauce_amount']}）" if o["sauce"] else "不要酱")
    print("耐心：",o["patience"],"回合")
    print("顾客重点：",o["focus"])
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
    print("装修：","、".join(k for k,v in state.get("renovations",{}).items() if v) or "暂无")
    print(f"当前订单：{state['order_pointer']+1}/{len(state['current_orders'])}｜本单已用回合：{state['turn']}")
    show_grill(state)
    print("已取出：",state["cooked"] or "无")
    print("组装："," → ".join(state["layers"]) or "未开始")
    print("酱料：",state["sauces"] or "无")

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
    r=evaluate(state,o)
    state["scores"].append(r["total"])
    state["revenue"]+=r["paid"]
    state["tips"]+=r["tip"]
    profit_bonus=2 if weekly_goal_bonus(state,"profit") else 0
    earned=r["paid"]+r["tip"]+profit_bonus
    state["coins"]+=earned
    state["daily_gross"]+=earned

    print("\n=== 出餐评分 ===")
    print(f"准确度 {r['accuracy']}/40")
    print(f"火候 {r['fire']}/25")
    print(f"摆放 {r['plating']}/15")
    print(f"速度 {r['speed']}/20")
    print(f"总分 {r['total']}/100")
    for d in r["details"]: print("-",d)
    print(f"本单收入：{r['paid']}｜小费：{r['tip']}｜目标奖励：{profit_bonus}")
    print(f"当前总金币：{state['coins']}")
    print(f"今日累计收入：{state['daily_gross']}")

    if r["total"]>=75:
        state["customer_progress"][o["customer"]]=state["customer_progress"].get(o["customer"],0)+1
    state["journal"].append(f"第{state['day']}天第{state['order_pointer']+1}单：{o['customer']}，{r['total']}分。")
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
status                         查看总金币、今日收入、烤台倒计时
orders                         查看当前订单
accept                         接单
grill beef                     放上牛肉饼
grill 牛肉饼                   中文也可以
flip 1                         翻1号烤位；翻面不消耗回合
wait                           等待1回合
take 1                         取出1号烤位食材
build bun lettuce beef bun     英文组装
build 原味胚 生菜 牛肉饼 原味胚  中文组装
sauce ketchup light            英文加酱
sauce 番茄酱 少量               中文加酱
serve                          出餐
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
status 会直接显示“再X回合到目标熟度”。
翻面不推进时间；等待和其他耗时操作才推进火候。
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
