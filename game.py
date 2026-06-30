
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
《午间汉堡铺》v0.4
给 AI 当玩家的 7 天汉堡店经营游戏。
重点：
- 7 天完整营业
- 订单随机生成
- 顾客偏好与忌口
- 修正速度评分：按“最少合理操作数”计算，不再让满操作也天然吃亏
- 自动存档
"""

from __future__ import annotations
import json
import random
from pathlib import Path
from typing import Any
from collections import Counter

BASE = Path(__file__).resolve().parent
SAVE_FILE = BASE / "save.json"

DAY_ORDER_COUNT = {1: 5, 2: 5, 3: 6, 4: 6, 5: 7, 6: 7, 7: 8}

UNLOCKS = {
    1: ["原味胚","牛肉饼","鸡肉饼","芝士","生菜","番茄","番茄酱"],
    2: ["全麦胚","洋葱","酸黄瓜","蛋黄酱"],
    3: ["培根","煎蛋"],
    4: ["辣酱"],
    5: ["双层汉堡","批量订单"],
    6: ["隐藏菜单"],
    7: ["唐九"],
}


RENOVATIONS = {
    "窗边花架": {
        "cost": 80,
        "desc": "所有顾客耐心+1",
        "effect": "patience"
    },
    "暖色吊灯": {
        "cost": 120,
        "desc": "每天结算时声誉额外+1",
        "effect": "reputation"
    },
    "加宽操作台": {
        "cost": 150,
        "desc": "组装汉堡不再推进时间",
        "effect": "build_time"
    },
    "高级烤台": {
        "cost": 180,
        "desc": "烤位从2个增加到3个",
        "effect": "grill_slot"
    },
    "自动酱料机": {
        "cost": 160,
        "desc": "酱料操作不再推进时间",
        "effect": "sauce_time"
    },
    "招牌照片墙": {
        "cost": 140,
        "desc": "摆放分最低保底为8分",
        "effect": "plating_floor"
    },
    "舒适候餐区": {
        "cost": 220,
        "desc": "所有顾客耐心再+2",
        "effect": "patience2"
    },
    "霓虹招牌": {
        "cost": 260,
        "desc": "每单基础售价+2金币",
        "effect": "price"
    }
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
    "bun":"原味胚","whole":"全麦胚","beef":"牛肉饼","chicken":"鸡肉饼","bacon":"培根",
    "egg":"煎蛋","cheese":"芝士","lettuce":"生菜","tomato":"番茄","onion":"洋葱",
    "pickle":"酸黄瓜","ketchup":"番茄酱","mayo":"蛋黄酱","chili":"辣酱"
}

INITIAL_STATE = {
    "version":"0.4",
    "shop_name":"",
    "chef_name":"",
    "sign_style":"",
    "day":1,
    "coins":80,
    "reputation":0,
    "scores":[],
    "revenue":0,
    "tips":0,
    "current_orders":[],
    "order_pointer":0,
    "current_order_accepted":False,
    "turn":0,
    "grill":{"1":None,"2":None},
    "cooked":[],
    "layers":[],
    "sauces":{},
    "customer_progress":{},
    "style":{"稳妥":0,"极速":0,"精致":0,"创新":0,"熟客":0,"利润":0},
    "journal":[],
    "finished":False,
    "week":1,
    "weekly_goal":"均衡经营",
    "renovations":{},
    "weekly_history":[],
    "daily_gross":0,
}

def clone_initial():
    return json.loads(json.dumps(INITIAL_STATE, ensure_ascii=False))

def save(state):
    SAVE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

def load():
    if SAVE_FILE.exists():
        state = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
        for k,v in INITIAL_STATE.items():
            state.setdefault(k, json.loads(json.dumps(v, ensure_ascii=False)))
        return state
    return clone_initial()

def setup(state):
    if state["shop_name"]:
        return
    print("欢迎来到《午间汉堡铺》v0.4。")
    state["shop_name"] = input("请给你的店起名：\n> ").strip() or "无名汉堡铺"
    state["chef_name"] = input("请给主厨起名：\n> ").strip() or "无名主厨"
    print("招牌风格：1温馨 2复古 3极简 4怪诞")
    state["sign_style"] = {"1":"温馨","2":"复古","3":"极简","4":"怪诞"}.get(input("> ").strip(),"温馨")
    state["journal"].append(f"{state['shop_name']}开张，主厨{state['chef_name']}，招牌风格{state['sign_style']}。")
    save(state)

def unlocked(day):
    items = []
    for d in range(1, min(day, 7)+1):
        items.extend(UNLOCKS.get(d, []))
    return set(items)

def available_customers(day):
    pool = [c for c in CUSTOMERS if c["name"] != "唐九"]
    if day >= 7:
        pool.append(next(c for c in CUSTOMERS if c["name"] == "唐九"))
    return pool


def has_renovation(state, name):
    return bool(state.get("renovations", {}).get(name))

def renovation_patience_bonus(state):
    bonus = 0
    if has_renovation(state, "窗边花架"):
        bonus += 1
    if has_renovation(state, "舒适候餐区"):
        bonus += 2
    return bonus

def weekly_goal_bonus(state, category):
    goal = state.get("weekly_goal", "均衡经营")
    mapping = {
        "速度优先": "speed",
        "精致摆盘": "plating",
        "顾客至上": "accuracy",
        "利润冲刺": "profit",
    }
    return mapping.get(goal) == category

def generate_order(state, day, customer):
    avail = unlocked(day)
    buns = ["原味胚"] + (["全麦胚"] if "全麦胚" in avail else [])
    bun = random.choice(buns)

    vegetarian = customer["name"] == "伊芙"
    proteins = []
    if vegetarian:
        if "煎蛋" in avail:
            proteins = ["煎蛋"]
        else:
            proteins = []
    else:
        proteins = [p for p in ["牛肉饼","鸡肉饼"] if p in avail]
        if day >= 3 and "煎蛋" in avail and random.random() < 0.2:
            proteins.append("煎蛋")
    if not proteins:
        protein = None
    else:
        liked = [p for p in proteins if p in customer["likes"]]
        protein = random.choice(liked or proteins)

    toppings_pool = [x for x in ["芝士","生菜","番茄","洋葱","酸黄瓜","培根"] if x in avail]
    toppings_pool = [x for x in toppings_pool if x not in customer["dislikes"]]
    count = random.randint(1, min(4, max(1,len(toppings_pool))))
    toppings = random.sample(toppings_pool, count) if toppings_pool else []

    if customer["focus"] == "portion" and day >= 5 and protein in ["牛肉饼","鸡肉饼"]:
        toppings.append(protein)

    sauces_pool = [x for x in ["番茄酱","蛋黄酱","辣酱"] if x in avail and x not in customer["dislikes"]]
    sauce = random.choice(sauces_pool) if sauces_pool and random.random() < 0.75 else None
    sauce_amount = random.choice(["少量","正常"]) if sauce else None

    doneness = None
    if protein == "牛肉饼":
        doneness = random.choice(["嫩","正好"])
    elif protein == "鸡肉饼":
        doneness = "正好"
    elif protein == "煎蛋":
        doneness = random.choice(["流心","全熟"])

    # 构造标准层次：下胚 -> 配菜 -> 主食材 -> 芝士/配菜 -> 上胚
    layers = [bun]
    lower = [x for x in toppings if x in ["生菜","番茄","洋葱","酸黄瓜"]]
    hot = [x for x in toppings if x in ["芝士","培根"]]
    layers.extend(lower[:2])
    if protein:
        layers.append(protein)
    layers.extend(hot)
    layers.extend(lower[2:])
    layers.append(bun)

    base_price = 12 + len(toppings)*2 + (5 if protein else 0) + (2 if sauce else 0)
    if toppings.count(protein) > 0:
        base_price += 5

    # 修正速度：耐心 = 最少合理操作数 + 顾客缓冲
    # accept不耗时；烹饪约3-4回合，build 1，sauce 1，serve不耗时
    min_ops = 4 + (1 if sauce else 0)
    patience = min_ops + max(2, customer["patience"] - 6) + renovation_patience_bonus(state)

    return {
        "customer":customer["name"],
        "focus":customer["focus"],
        "patience":patience,
        "base_price":base_price + (2 if has_renovation(state, "霓虹招牌") else 0),
        "bun":bun,
        "protein":protein,
        "doneness":doneness,
        "toppings":toppings,
        "sauce":sauce,
        "sauce_amount":sauce_amount,
        "required_layers":layers,
        "dislikes":customer["dislikes"],
        "tip_mult":customer["tip"],
    }

def generate_day(state):
    random.seed()
    count = DAY_ORDER_COUNT.get(state["day"], min(10, 8 + (state["week"] - 1) // 2))
    customers = random.choices(available_customers(state["day"]), k=count)
    state["current_orders"] = [generate_order(state, state["day"], c) for c in customers]
    state["order_pointer"] = 0
    state["scores"] = []
    state["revenue"] = 0
    state["tips"] = 0
    state["daily_gross"] = 0
    state["current_order_accepted"] = False
    state["turn"] = 0
    state["grill"] = {"1":None,"2":None,"3":None} if has_renovation(state, "高级烤台") else {"1":None,"2":None}
    state["cooked"] = []
    state["layers"] = []
    state["sauces"] = {}
    save(state)

def current_order(state):
    if state["order_pointer"] >= len(state["current_orders"]):
        return None
    return state["current_orders"][state["order_pointer"]]

def describe_order(o):
    print(f"\n【第{o_index(o)}单｜{o['customer']}】")
    print("面包：", o["bun"])
    print("层次（从下到上）：", " → ".join(o["required_layers"]))
    print("主食材：", o["protein"] or "无肉")
    print("熟度：", o["doneness"] or "无")
    print("酱料：", f"{o['sauce']}（{o['sauce_amount']}）" if o["sauce"] else "不要酱")
    print("耐心：", o["patience"])

def o_index(o):
    # 仅用于展示，实际由外层覆盖
    return "当前"

def advance(state, steps=1):
    state["turn"] += steps
    for item in state["grill"].values():
        if item:
            item["time"] += steps

def doneness(protein, t):
    if protein == "牛肉饼":
        return "生" if t<=1 else "嫩" if t==2 else "正好" if t==3 else "焦熟" if t==4 else "烧焦"
    if protein == "鸡肉饼":
        return "未熟" if t<=2 else "正好" if t==3 else "偏干" if t==4 else "烧焦"
    if protein == "煎蛋":
        return "流心" if t<=2 else "全熟" if t==3 else "焦"
    if protein == "培根":
        return "软" if t<=1 else "脆" if t==2 else "焦"
    return "未知"

def grill(state, token):
    p = ALIASES.get(token)
    if p not in ["牛肉饼","鸡肉饼","煎蛋","培根"]:
        print("可烹饪：beef / chicken / egg / bacon")
        return
    slot = next((k for k,v in state["grill"].items() if v is None), None)
    if not slot:
        print("烤台已满。")
        return
    state["grill"][slot] = {"protein":p,"time":0,"flipped":False}
    advance(state)
    print(f"{p}放上{slot}号烤位。")

def flip(state, slot):
    item = state["grill"].get(slot)
    if not item:
        print("这个烤位为空。"); return
    if item["flipped"]:
        print("已经翻过面。"); return
    item["flipped"] = True
    advance(state)
    print(f"{slot}号烤位已翻面。")

def take(state, slot):
    item = state["grill"].get(slot)
    if not item:
        print("这个烤位为空。"); return
    item["doneness"] = doneness(item["protein"], item["time"])
    state["cooked"].append(item)
    state["grill"][slot] = None
    advance(state)
    print(f"取出{item['protein']}，熟度：{item['doneness']}。")

def build(state, tokens):
    layers = []
    for t in tokens:
        if t not in ALIASES:
            print("无法识别：", t); return
        layers.append(ALIASES[t])
    state["layers"] = layers
    if not has_renovation(state, "加宽操作台"):
        advance(state)
    print("已组装：", " → ".join(layers))

def add_sauce(state, token, amount):
    name = ALIASES.get(token)
    if name not in ["番茄酱","蛋黄酱","辣酱"]:
        print("酱料：ketchup / mayo / chili"); return
    amap = {"light":"少量","normal":"正常","heavy":"过量"}
    if amount not in amap:
        print("用量：light / normal / heavy"); return
    state["sauces"][name] = amap[amount]
    if not has_renovation(state, "自动酱料机"):
        advance(state)
    print(f"已加入{name}：{amap[amount]}。")

def evaluate(state, o):
    details=[]
    accuracy, fire, plating, speed = 40,25,15,20

    a=Counter(state["layers"]); e=Counter(o["required_layers"])
    missing=list((e-a).elements()); extra=list((a-e).elements())

    if missing:
        p=min(24,6*len(missing)); accuracy-=p; details.append(f"缺少{'、'.join(missing)} -{p}")
    if extra:
        p=min(20,5*len(extra)); accuracy-=p; details.append(f"多余{'、'.join(extra)} -{p}")

    for bad in o["dislikes"]:
        if bad in state["layers"] or bad in state["sauces"]:
            accuracy-=15; details.append(f"触发忌口：{bad} -15")

    if o["sauce"]:
        actual=state["sauces"].get(o["sauce"])
        if actual is None:
            accuracy-=8; details.append(f"缺少{o['sauce']} -8")
        elif actual!=o["sauce_amount"]:
            accuracy-=5; details.append(f"{o['sauce']}用量错误 -5")
        for s in state["sauces"]:
            if s!=o["sauce"]:
                accuracy-=6; details.append(f"多加酱料{s} -6")
    elif state["sauces"]:
        accuracy-=10; details.append("本单不要酱 -10")

    if o["protein"]:
        cooked = next((x for x in state["cooked"] if x["protein"]==o["protein"]), None)
        if not cooked:
            fire=0; details.append("主食材未完成 -25")
        else:
            if cooked["doneness"]!=o["doneness"]:
                fire-=12; details.append(f"熟度{o['doneness']}，实际{cooked['doneness']} -12")
            if not cooked["flipped"] and o["protein"] in ["牛肉饼","鸡肉饼"]:
                fire-=5; details.append("未翻面 -5")

    if state["layers"] != o["required_layers"]:
        common=sum(1 for i,x in enumerate(state["layers"]) if i<len(o["required_layers"]) and x==o["required_layers"][i])
        plating=int(15*common/max(1,len(o["required_layers"])))
        details.append(f"层次顺序部分正确 {plating}/15")

    patience_left = o["patience"] - state["turn"]
    if patience_left >= 2:
        speed=20
    elif patience_left==1:
        speed=17
    elif patience_left==0:
        speed=13
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

    if has_renovation(state, "招牌照片墙"):
        plating = max(plating, 8)
    if weekly_goal_bonus(state, "speed"):
        speed = min(20, speed + 2)
    if weekly_goal_bonus(state, "plating"):
        plating = min(15, plating + 2)
    if weekly_goal_bonus(state, "accuracy"):
        accuracy = min(40, accuracy + 2)
    accuracy=max(0,min(40,accuracy)); fire=max(0,min(25,fire))
    plating=max(0,min(15,plating)); speed=max(0,min(20,speed))
    total=max(0,min(100,accuracy+fire+plating+speed))

    paid=o["base_price"] if total>=40 else 0
    tip=0
    if total>=90: tip=int(o["base_price"]*0.30*o["tip_mult"])
    elif total>=75: tip=int(o["base_price"]*0.10*o["tip_mult"])

    return {"accuracy":accuracy,"fire":fire,"plating":plating,"speed":speed,
            "total":total,"paid":paid,"tip":tip,"details":details}

def reset_workspace(state):
    state["current_order_accepted"]=False
    state["turn"]=0
    state["grill"]={"1":None,"2":None,"3":None} if has_renovation(state, "高级烤台") else {"1":None,"2":None}
    state["cooked"]=[]
    state["layers"]=[]
    state["sauces"]={}

def serve(state):
    o=current_order(state)
    if not o:
        print("今天没有订单。"); return
    if not state["current_order_accepted"]:
        print("请先 accept。"); return
    r=evaluate(state,o)
    state["scores"].append(r["total"])
    state["revenue"]+=r["paid"]
    state["tips"]+=r["tip"]
    profit_bonus = 2 if weekly_goal_bonus(state, "profit") else 0
    state["coins"]+=r["paid"]+r["tip"]+profit_bonus
    state["daily_gross"] = state.get("daily_gross", 0) + r["paid"] + r["tip"] + profit_bonus
    if profit_bonus:
        print("本周目标“利润冲刺”额外收入 +2")
    if r["total"]>=75:
        state["customer_progress"][o["customer"]] = state["customer_progress"].get(o["customer"],0)+1
    print("\n=== 出餐评分 ===")
    print(f"准确度 {r['accuracy']}/40")
    print(f"火候 {r['fire']}/25")
    print(f"摆放 {r['plating']}/15")
    print(f"速度 {r['speed']}/20")
    print(f"总分 {r['total']}/100")
    for d in r["details"]: print("-",d)
    print(f"收入 {r['paid']}｜小费 {r['tip']}")
    print(f"当前总金币：{state['coins']}")
    print(f"今日累计收入：{state.get('daily_gross', 0)}")
    state["journal"].append(f"第{state['day']}天第{state['order_pointer']+1}单：{o['customer']}，{r['total']}分。")
    state["order_pointer"]+=1
    reset_workspace(state)
    if state["order_pointer"]>=len(state["current_orders"]):
        finish_day(state)
    save(state)


def choose_weekly_goal(state):
    print("\n请选择下一周经营目标：")
    goals = ["均衡经营", "速度优先", "精致摆盘", "顾客至上", "利润冲刺"]
    for i, goal in enumerate(goals, 1):
        print(f"{i}. {goal}")
    raw = input("> ").strip()
    if raw.isdigit() and 1 <= int(raw) <= len(goals):
        state["weekly_goal"] = goals[int(raw)-1]
    else:
        state["weekly_goal"] = "均衡经营"
    print("下一周目标：", state["weekly_goal"])

def renovation_shop(state):
    while True:
        print("\n=== 店铺装修 ===")
        print("金币：", state["coins"])
        items = list(RENOVATIONS.items())
        for i, (name, info) in enumerate(items, 1):
            owned = "【已拥有】" if has_renovation(state, name) else f"{info['cost']}金币"
            print(f"{i}. {name} - {owned} - {info['desc']}")
        print("0. 离开装修店")
        raw = input("> ").strip()
        if raw == "0":
            break
        if not raw.isdigit() or not 1 <= int(raw) <= len(items):
            print("无效选择。")
            continue
        name, info = items[int(raw)-1]
        if has_renovation(state, name):
            print("已经拥有这项装修。")
            continue
        if state["coins"] < info["cost"]:
            print("金币不足。")
            continue
        state["coins"] -= info["cost"]
        state.setdefault("renovations", {})[name] = True
        print(f"已购买：{name}。{info['desc']}")
        state["journal"].append(f"购入装修：{name}。")
        save(state)

def finish_day(state):
    avg=round(sum(state["scores"])/len(state["scores"]),1)
    fixed=23 + max(0, state["week"]-1) * 2
    state["coins"]-=fixed
    bonus=20 if avg>=90 else 10 if avg>=75 else 0
    rep=8 if avg>=90 else 5 if avg>=75 else 2 if avg>=60 else -3
    if has_renovation(state, "暖色吊灯"):
        rep += 1
    state["coins"]+=bonus
    state["reputation"]+=rep
    print("\n====================")
    print(f"第{state['day']}天结算")
    print("====================")
    print("营业额：",state["revenue"])
    print("小费：",state["tips"])
    print(f"固定成本：-{fixed}")
    print("奖励：",bonus)
    print("平均分：",avg)
    print("金币：",state["coins"])
    print("声誉：",state["reputation"])
    available_renovations = [
        (name, info) for name, info in RENOVATIONS.items()
        if not has_renovation(state, name) and state["coins"] >= info["cost"]
    ]
    if available_renovations:
        cheapest_name, cheapest_info = min(available_renovations, key=lambda x: x[1]["cost"])
        print(f"【装修提醒】当前金币足够购买：{cheapest_name}（{cheapest_info['cost']}金币）")
        print("可输入 renovate 打开装修商店。")
    else:
        print("【装修提醒】继续攒金币，达到装修价格后可输入 renovate。")
    state["journal"].append(f"第{state['day']}天结束，平均分{avg}。")

    if state["day"] % 7 == 0:
        week_avg = avg
        rating = "S" if week_avg>=92 and state["coins"]>=250 else "A" if week_avg>=85 else "B" if week_avg>=75 else "C" if week_avg>=60 else "D"
        state["weekly_history"].append({
            "week": state["week"],
            "rating": rating,
            "coins": state["coins"],
            "reputation": state["reputation"]
        })
        print(f"\n第{state['week']}周完成！评级：{rating}")
        print("打烊后可以使用金币装修店铺。现在将自动打开装修商店。")
        renovation_shop(state)
        choose_weekly_goal(state)
        state["week"] += 1

    state["day"] += 1
    generate_day(state)
    if state["day"] <= 7:
        print(f"\n第{state['day']}天已解锁：", "、".join(UNLOCKS.get(state["day"],[])))
    else:
        print(f"\n进入第{state['day']}天，第{state['week']}周继续营业。")
    save(state)

def status(state):
    print(f"\n{state['shop_name']}｜主厨{state['chef_name']}")
    print(f"第{state['day']}天｜第{state['week']}周｜金币{state['coins']}｜声誉{state['reputation']}")
    print("本周目标：", state.get("weekly_goal", "均衡经营"))
    print("今日累计收入：", state.get("daily_gross", 0))
    print("装修：", "、".join(k for k,v in state.get("renovations",{}).items() if v) or "暂无")
    print(f"当前订单 {state['order_pointer']+1}/{len(state['current_orders'])}")
    print(f"本单回合 {state['turn']}")
    for k,v in state["grill"].items():
        print(k, "空" if not v else f"{v['protein']} 时间{v['time']} {'已翻面' if v['flipped'] else '未翻面'}")
    print("已取出：", state["cooked"])
    print("组装：", " → ".join(state["layers"]) or "未开始")
    print("酱料：", state["sauces"])

HELP = """
指令：
status
orders
accept
grill beef|chicken|egg|bacon
flip 1
take 1
wait
build bun lettuce beef cheese bun
sauce ketchup|mayo|chili light|normal|heavy
serve
renovate
save
quit

食材别名：
bun 原味胚
whole 全麦胚
beef 牛肉饼
chicken 鸡肉饼
bacon 培根
egg 煎蛋
cheese 芝士
lettuce 生菜
tomato 番茄
onion 洋葱
pickle 酸黄瓜
ketchup 番茄酱
mayo 蛋黄酱
chili 辣酱
"""

def show_current(state):
    o=current_order(state)
    if not o:
        print("今天没有订单。"); return
    print(f"\n【第{state['order_pointer']+1}单｜{o['customer']}】")
    print("层次："," → ".join(o["required_layers"]))
    print("熟度：",o["doneness"] or "无")
    print("酱料：",f"{o['sauce']} {o['sauce_amount']}" if o["sauce"] else "不要酱")
    print("耐心：",o["patience"])

def main():
    state=load()
    setup(state)
    if not state["current_orders"] and not state["finished"]:
        generate_day(state)
    print(f"\n欢迎回到「{state['shop_name']}」。")
    show_current(state)
    print(HELP)
    while True:
        raw=input("\n> ").strip()
        if not raw: continue
        p=raw.split(); cmd=p[0].lower()
        if cmd=="status": status(state)
        elif cmd=="orders": show_current(state)
        elif cmd=="accept":
            state["current_order_accepted"]=True; print("已接单。")
        elif cmd=="grill" and len(p)==2: grill(state,p[1].lower())
        elif cmd=="flip" and len(p)==2: flip(state,p[1])
        elif cmd=="take" and len(p)==2: take(state,p[1])
        elif cmd=="wait": advance(state); print("等待1回合。")
        elif cmd=="build" and len(p)>1: build(state,[x.lower() for x in p[1:]])
        elif cmd=="sauce" and len(p)==3: add_sauce(state,p[1].lower(),p[2].lower())
        elif cmd=="serve":
            serve(state)
            if not state["finished"]: show_current(state)
        elif cmd=="renovate": renovation_shop(state)
        elif cmd=="save": save(state); print("已保存。")
        elif cmd=="help": print(HELP)
        elif cmd=="quit": save(state); print("已保存并退出。"); break
        else: print("无法识别。输入 help。")
        save(state)

if __name__=="__main__":
    main()
