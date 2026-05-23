# Pawspective / 地球Online小狗服

移动端优先的趣味 H5 图片生成器。用户上传小狗照片后，前端读取图片并请求本地 FastAPI 后端，后端返回小狗视角的“地球副本测评”，页面在 3/4 弹窗内渲染可保存的打卡卡片。

## 当前阶段

当前是前后端 MVP 闭环，并已完成移动端弹窗化改造：

- `index.html`：移动端 H5 主页面，包含上传、3/4 结果弹窗、保存图片、抽屉菜单、Demo 轮播、副本切换和规则播报。
- `page_config.json`：页面文案、按钮、规则、菜单、卡片默认文案的独立配置文件。`index.html` 会优先 `fetch` 该文件，失败时回退到内置 fallback。
- `main.py`：FastAPI 后端，接收图片上传并返回 VLM 风格 JSON。当前支持随机抽象回退，也保留模型类型标记。
- `demo1.jpg` 到 `demo4.jpg`：顶部 Demo 展示区素材。
- `html2canvas` 导出逻辑：前端将弹窗内临时渲染的固定 400px 宽卡片保存为 PNG。

## 页面区域

当前主页面从上到下大致如下：

```text
┌────────────────────────────┐
│ 右上：🐾 抽屉入口             │
│                            │
│      Demo 展示区             │
│   demo1-4 错落轮播           │
│                            │
│ 🌍 地球 OnLine              │
│ 当前已接入：小狗服...         │
│                            │
│ 🎮 副本切换栏                │
│ 神秘草地 / 拖鞋 / 飞行物      │
│                            │
│ 📸 上传小狗照片              │
│ 游戏规则播报栏               │
│                            │
│ 生成中：Loading 状态          │
└────────────────────────────┘

生成完成弹窗：
┌────────────────────────────┐
│ 半透明毛玻璃遮罩             │
│ ┌────────────────────────┐ │
│ │ 右上：× 关闭             │ │
│ │                        │ │
│ │ 3/4 高度结果弹窗         │ │
│ │ #captureCard 临时卡片    │ │
│ │ #modal-image-view 图片  │ │
│ │                        │ │
│ │ 保存图片 / 再来一张       │ │
│ │ 新狗额外展示：创建档案    │ │
│ └────────────────────────┘ │
└────────────────────────────┘

右侧抽屉：
┌───────────────┬────────────┐
│ 半透明遮罩     │ 75vw 抽屉   │
│ 点击关闭       │ 菜单列表     │
└───────────────┴────────────┘
```

主页面不再保留生成结果卡片，也没有页面下方预览残留。生成完成后，前端会在弹窗内临时创建 `#captureCard`，其中上传图片节点为 `#modal-image-view`。该图片区域固定为 1:1 正方形，并通过 `object-fit: cover` 居中裁剪填满，不拉伸变形。关闭弹窗会清空图片 `src`、销毁弹窗内容并恢复上传前状态。

## 配置文件

`page_config.json` 是当前唯一的页面文案配置入口，主要结构如下：

```json
{
  "meta": {},
  "game_rules": [],
  "buttons": {},
  "quests": [],
  "models": [],
  "drawer": [],
  "card": {},
  "status": {},
  "modal": {}
}
```

修改页面文案、按钮、规则播报、菜单项时，优先改 `page_config.json`。`index.html` 中仍保留同结构 fallback，用于 `fetch` 失败时兜底，避免页面白屏。

## 后端接口

`POST /api/upload-dog-pic`

请求：

- `multipart/form-data`
- 字段名：`file`
- 类型：图片文件

当前 mock 返回：

```json
{
  "success": true,
  "review": "好评！今天在这个绿茵大副本刷到了会飞的盘子，虽然没咬住但渲染画质极高，空气里有土和肉垫的香味，推荐所有修仙狗勾来刷！",
  "rating": 5,
  "model_type": "随机抽象",
  "exp_gained": 35
}
```

前端收到后会：

- 在弹窗内临时创建 `#captureCard`
- 将上传图片 URL 赋给 `#modal-image-view`
- 写入评分、测评文案和 `model_type` 标签
- 按 `exp_gained` 增加副本经验
- 展示保存、再来一张按钮；如果 `localStorage.has_dog_profile !== "true"`，额外展示创建档案按钮

## 运行方式

建议使用项目 conda 环境：

```bash
cd /Users/littleyog/Projects/earth-online-pup/EarthOnline-PupServer
conda activate earth-online-pup
```

安装后端依赖：

```bash
pip install fastapi uvicorn python-multipart
```

启动后端：

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

启动前端静态服务：

```bash
python -m http.server 8010
```

访问：

```text
http://localhost:8010/index.html
```

## 注意事项

- 前端目前只接受 `.jpg/.jpeg/.png`。
- 前端请求固定指向 `http://127.0.0.1:8000/api/upload-dog-pic`。
- 后端开启 CORS，允许本地静态页面跨域访问。
- TailwindCSS 目前通过 CDN 加载，离线环境需改成本地依赖。
- `constants.js` 已不再被 `index.html` 引用；旧规则已迁移到 `page_config.json`。
