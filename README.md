# 《午间汉堡铺》v0.6

一款适合 AI 或人类玩家运行的命令行汉堡店经营游戏。

## v0.6 主要更新

- 火候达到目标时明确提示立即 `take`
- `take` 与 `flip` 明确不消耗回合
- 顾客专精在订单与评分里完整显示
- 真实批量订单：每份汉堡都要单独完成并放上托盘
- 双层汉堡真正需要两份主食材
- 原创配方、顾客试吃与隐藏菜单
- 顾客评分后会给出符合个性的反馈
- 四种招牌风格都会实际影响经营
- 新增 `check`、`undo build`、`clear sauce`、`discard`
- 新增顾客档案、营业记录与原创配方查看

## 运行

```bash
python game.py
```

首次运行会要求设置店名、主厨名与招牌风格，并在当前目录生成 `save.json`。

## 常用指令

```text
status
orders
accept
grill beef
flip 1
wait
take 1
build bun lettuce beef bun
sauce ketchup light
check
plate
tray
serve
```

### 批量订单

批量订单中，每一份汉堡都要单独完成：

```text
build ...
plate
build ...
plate
tray
serve
```

### 隐藏菜单

第 6 天后开放：

```text
create 月光汉堡
test 月光汉堡
recipes
```

先组装样品，再使用 `create 配方名` 保存。邀请不同顾客试吃后，符合条件的原创配方会正式上架，并在匹配出餐时提供额外收入。

## 补救与信息指令

```text
check
undo build
clear sauce
discard 1
customer 伊芙
history
```

## 存档

游戏会自动保存到同目录的 `save.json`。继续游戏时，请保留 `game.py` 与 `save.json`。
