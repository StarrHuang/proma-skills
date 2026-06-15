---
name: men-tshirt-Moikrakki
description: >
  为 Moikrakki 品牌男士 T恤 生成整套亚马逊 Premium A+ 图片生成 Prompt。
  当用户提到 Moikrakki、男士T恤、A+设计、亚马逊 A+ Content 生成、T恤 A+ 图片 prompt 时触发。
  用户提供商品信息（颜色、面料、款式、卖点、尺码），本 skill 输出 7 个可直接用于 GPT Image / Midjourney 的完整 prompt 模块。
  这是品类特定变体（T恤），区别于已存在的 men-tshirt-Moikrakki 同族 skill。
---

# Moikrakki 男士 T恤 A+ Prompt 生成器

## 核心原则

> 你的工作是**转换**，不是创作。用户提供商品信息，你输出 7 个格式标准、细节到位、可直接生图的 prompt。不要反问用户要更多信息——用户给什么就用什么，缺失的部分用合理默认值填充并在文件中标注 `[默认值]`。

### 与衬衫版 prompt 的关键区别（T恤专属调整）

| 项 | 衬衫版 | T恤版 |
|----|--------|-------|
| 核心卖点方向 | 防污/免烫/弹力/商务 | 面料舒适/透气/版型/休闲百搭 |
| 模特姿态 | 挺拔、商务精英 | 松弛、日常、街头感 |
| 领口特写 | Spread Collar / Button Cuff | Crew Neck / V-Neck 领口罗纹 |
| 面料展示 | 防污疏水微距 | 棉质/混纺面料肌理、透气孔 |
| 场景重心 | 办公室 + 咖啡店 + 通勤 | 街头 + 户外 + 居家 + 社交 |
| 印花/图案 | 无（素色商务） | 可包含印花/Logo/图案特写 |
| 品牌调性 | 阳刚儒雅、精英感 | 都市松弛、年轻活力 |

### 工作流程

1. **收集信息** — 读取用户提供的商品信息，如果没有明确提供，使用以下默认值填充并在所有 prompt 中标注 `[默认值]`：
   - 颜色：White
   - 面料：100% Cotton / Cotton blend
   - 款式：Crew Neck Short Sleeve
   - 核心卖点：Soft, Breathable, Comfort Fit
   - 尺码：S-2XL
2. **输出 7 个 prompt 模块** — 每个模块包含完整英文 prompt，所有可变内容用 `{花括号}` 标注
3. **附带设计规范速查表** — 颜色、字体、尺寸
4. **附带模块搭配建议** — Premium 和 Basic 两套方案

---

## 全局品牌设计规范（所有 prompt 必须嵌入）

```
品牌配色:
- 背景主色: #F2F0EB（暖灰白）
- 深色背景: #2C2C2C（深炭灰，用于功能模块）
- 标题文字: #000000（纯黑）
- 正文文字: #333333 / #555555 / #888888（深灰三级）
- 强调色: #1A2744（海军蓝）

字体体系:
- 品牌Logo / 主标题: EightiesComeback Semi Bold Condensed，全大写
- 副标题 / 功能标签: EightiesComeback Semi Bold Condensed 或 Helvetica Neue Light
- 正文 / 说明: Helvetica Neue Light / Regular
- 尺码表: Helvetica Neue Regular

通用负面 Prompt（所有模块必加）:
- 禁止: no gradient, no shadow blocks, no cartoon style, no neon colors, no over-retouching, no cheap e-commerce poster vibe, no watermarks, no promotional badges, no price tags, no UI components, no decorative graphics, no glossy plastic skin, no CGI texture, no fake symmetrical faces, no anime facial features, no heavy filters, no blurry edges, no noisy background, no cluttered props, no 3D render look

设计美学: 奢侈男装品牌广告 × 亚马逊 Premium A+ 排版 × 真实素人质感。留白充足、边缘锐利、真实摄影质感、构图精确、杂志级排版。
```

---

## 模块输出格式

每个模块按以下结构输出：

```
### 模块 N：{模块名称}
**用途**: {用途说明}
**尺寸**: {宽度}×{高度} px
**尺寸备注**: {Premium/Basic 的尺寸差异说明}

```
{prompt 全文}
```
```

---

## 7 个模块模板

### 模块一：Brand Hero Banner

**用途**: A+ 首图，建立品牌认知与产品第一印象
**尺寸**: 1464 × 600 px（Premium）/ 970 × 600 px（Basic）
**尺寸备注**: Premium A+ 用 1464px 宽度，Basic A+ 用 970px

```
生成一张亚马逊A+男装T恤banner，横版超宽画幅（比例约2.44:1），背景为均匀纯色暖灰白（#F2F0EB），图片尺寸为{1464×600——若Basic A+则改为970×600}，整体风格为极简高端男装时尚杂志风，无任何纹理、无渐变、无阴影块。

画面采用严格三栏结构：左侧模特 + 中间文字 + 右侧模特。中间完全居中对称，左右视觉平衡但不对称。

左侧放置一名男性模特，身穿{目标T恤——品牌Moikrakki，款式为{款式，如Crew Neck Short Sleeve}，颜色为{颜色，如White}}，搭配{下装搭配，如修身牛仔裤或休闲卡其裤}，身体微微向中间倾斜，姿态自然松弛，一只手轻插裤袋，另一只手自然下垂或轻触领口，头部微微下压，眼神冷静自信。面部有真实皮肤纹理、轻微胡茬、自然光影。人物边缘干净抠图，贴近画布边缘但留少量留白。

右侧放置同一模特的上半身近景，画面裁切到胸部以下区域，头部被部分裁掉或仅露下巴到领口，画面右侧直接裁切出界，人物略微侧身（不超过15度），重点展示T恤的领口罗纹结构、面料纹理、肩部缝合线、以及{印花/图案位置，如有}细节。人物占比明显大于左侧。

中间为文字排版区域，全部居中对齐：
- 顶部小字为品牌logo MOIKRAKKI，EightiesComeback Semi Bold Condensed字体，字间距宽松，纯黑色；
- 中间为两行主标题，文案为{主标题，如EVERYDAY ESSENTIAL TEE}，全部大写，EightiesComeback Semi Bold Condensed字体，字体尺寸占画面高度约18-20%，具有奢侈品牌广告感；
- 下方为一段1-2行英文副标题，简述2-3个核心卖点，如{副标题文案，如Ultra-Soft Cotton · Breathable · Perfect Fit}，Helvetica Light字体，深灰色（#555555），字号约为主标题的25-30%；
- 副标题下方可放置3-4个产品核心卖点图标+文字小标签（{如柔软、透气、弹力、耐用}），极简线条图标，Helvetica字体，深灰色；
- 最下方居中排列产品颜色小圆点（{颜色列表，如White, Black, Navy, Gray}），大小一致、间距均匀。

整体要求：高端、干净、留白充足、真实摄影质感、边缘锐利。无多余元素、无装饰图形、无UI组件、无阴影块、无渐变、无噪点、无水印，视觉类似高端男装品牌广告与Amazon Premium A+页面结合风格。{通用负面prompt}
```

### 模块二：Core Feature Highlights

**用途**: 展示 T恤 核心卖点（面料、版型、领口、搭配），中心模特+环绕细节裁切
**尺寸**: 1464 × 1200 px（Premium）/ 970 × 600 px（Basic）
**尺寸备注**: Premium 为竖版超宽，Basic 为横版

**Premium 版（1464×1200）：**

```
生成一张亚马逊A+男装T恤功能展示图，横版画幅（比例约1.22:1），背景为纯色暖灰白（#F2F0EB），图片尺寸为1464×1200，极简高端男装时尚杂志风，无渐变、无阴影块。所有标题使用EightiesComeback Semi Bold Condensed字体。

画面中心放置一名男性模特，全身三分之二站立（膝盖以上），身穿{目标T恤——颜色为{颜色}}，搭配{下装搭配}，姿态自然挺拔但松弛。右手轻插裤袋，左手自然下垂或轻触前胸面料，肩部放松，头部微微下压，眼神冷静直视前方。人物居中略偏上，占画面高度约65-70%。T恤面料需展示真实棉质纹理、轻微自然褶皱、领口罗纹挺括有型。模特真实皮肤质感、自然光影。

左上区域放置一个完美圆形裁切图，展示{卖点一细节——如领口-Crew Neck罗纹结构特写}。圆形边缘干净。下方居中标注英文名称：{卖点一名称，如CREW NECK RIBBING}，EightiesComeback Semi Bold Condensed字体，黑色。

右上区域放置一个圆角矩形图（圆角约25px），展示{卖点二细节——如面料微距纹理或透气孔结构}。上方右对齐标注：{卖点二名称，如COTTON JERSEY TEXTURE}，EightiesComeback Semi Bold Condensed字体，纯黑。

右下区域放置一个圆形裁切图，展示{卖点三细节——如肩部缝合/袖口车线/印花细节}。下方标注：{卖点三名称，如NEAT STITCHING DETAIL}，EightiesComeback Semi Bold Condensed字体，黑色。

左下区域放置{卖点四——如搭配Flat Lay}，包括太阳镜、手表、休闲鞋、牛仔裤等配饰，排列自然视觉平衡，不重叠。

在中间主模特与周边细节图之间可添加极细手绘感弯曲箭头（深灰色），从各细节图指向主模特对应位置，增强信息层次感。

{通用负面prompt}
```

**Basic 版（970×600）：**

```
生成一张亚马逊A+男装T恤功能展示图，横版画幅，背景为纯色暖灰白（#F2F0EB），图片尺寸为970×600，极简风格。

画面左右分区：
- 左侧（约50%）: 男性模特半身站立身穿{目标T恤}，展示正面整体效果，姿态自然，一手轻触面料。
- 右侧（约50%）: 上下排列2个圆形裁切细节图：
  · 上图: {卖点一——领口罗纹微距}
  · 下图: {卖点二——面料纹理微距}
  
左侧下方标注主标题{卖点主题，如PREMIUM COTTON}，右侧两图旁边各标注名称。所有标题使用EightiesComeback Semi Bold Condensed字体。

{通用负面prompt}
```

### 模块三：Fabric & Material Close-up

**用途**: 展示面料微距特写，强调材质质感、透气性、柔软度
**尺寸**: 970 × 600 px
**模块类型**: Standard Image with Text Overlay

```
生成一张亚马逊A+男装T恤面料材质展示图，横版画幅，图片尺寸为970×600，背景均匀纯色暖灰白（#F2F0EB），极简风格。

画面左右分区：

左侧（约55%）: 大尺寸面料微距特写——展示{目标T恤}面料的{编织纹理/透气孔/棉质纤维}结构，微距摄影（macro photography），景深自然，光影柔和，面料边缘清晰可见纱线条纹。画面裁切干净，无多余元素。面料上方或角落放置标签文字：{面料成分，如100% COTTON / COTTON BLEND}，EightiesComeback Semi Bold Condensed字体，深灰色。

右侧（约45%）: 展示面料的{特性——如拉伸回弹/透气性/柔软度}。
- 上半部分（可选）: 展示手部拉伸面料的效果，展示弹力和回弹性。
- 下半部分: 文字说明区，3行以内:
  • 第一行大号标题: {如SOFT · BREATHABLE · DURABLE}，EightiesComeback Semi Bold Condensed字体
  • 第二行细分说明（可选）: {面料科技，如Moisture-Wicking, Quick-Dry}，Helvetica Light字体
  • 小行文字: {面料成分 + 重量，如100% Ring-Spun Cotton, 180 GSM}，Helvetica Light字体，浅灰色

整体要求：微距摄影质感、面料纹理锐利清晰、光影柔和自然。无过度锐化、无噪点、无廉价产品图感。

{通用负面prompt}
```

### 模块四：Comfort & Fit Scene

**用途**: 展示T恤舒适度和版型的多场景应用
**尺寸**: 970 × 600 px
**模块类型**: Standard Image with Text / 双场景组合

```
生成一张亚马逊A+男装T恤舒适版型展示图，横版画幅，背景为均匀纯色暖灰白（#F2F0EB），图片尺寸为970×600，极简男装风格。

画面采用双场景左右或上下分区：

【场景一 - 日常休闲（左/上）】
男性模特身穿{目标T恤}，在{城市街头/公园/咖啡店门口}场景，日常站立或行走姿态，身体放松，展示T恤在自然状态下的版型：肩线位置贴合、下摆长度适中、身体活动自如。真实iPhone自然光拍摄质感，轻微生活化背景但不过度杂乱。

【场景二 - 动态活动（右/下）】
同一模特身穿同一件T恤，做{伸展/抬手/转身}等动作，展示T恤的弹力、透气性和运动自由度。面料在活动中自然拉伸但不紧绷，展示穿着舒适度。

两场景之间以细线或留白分隔。标题放置在左上或正上方中央：{主标题，如ALL-DAY COMFORT / BUILT FOR MOVEMENT}，EightiesComeback Semi Bold Condensed字体，纯黑色。

每个场景右下角或下方标注简短说明文字（Helvetica Light字体，深灰色）：
- 场景一: {如RELAXED FIT - Daily Essential}  
- 场景二: {如FULL RANGE - Stretch & Move}

整体要求：模特真实皮肤质感、自然光影、专注展现T恤穿着效果而非模特本身。无夸张姿势、无过度修图、无僵硬感。

{通用负面prompt}
```

### 模块五：Craftsmanship Details

**用途**: 展示领口、袖口、下摆、缝线、印花等工艺细节
**尺寸**: 970 × 600 px
**模块类型**: Standard Three Images

```
生成一张亚马逊A+男装T恤工艺细节展示图，横版画幅，背景为均匀纯色暖灰白（#F2F0EB），图片尺寸为970×600，极简高端男装风格。

画面采用网格布局——顶部大标题居中，下方3列细节图横向等距排列：

顶部中央大标题：{如EXQUISITE CRAFTSMANSHIP}，EightiesComeback Semi Bold Condensed字体，纯黑色，占画面高度约12%。

标题下方等距排列3张竖向细节图（每张比例约4:5）：
- 左图: {细节1——如领口Crew Neck罗纹特写}，裁切范围为领口区域，展示领口罗纹宽度、缝合工艺、定型效果。下方小字标注：{如REINFORCED CREW NECK}。
- 中图: {细节2——如袖口/下摆Double Stitching特写}，展示袖口或下摆的双针车线工艺，缝线笔直均匀。下方小字标注：{如DOUBLE STITCHED HEM}。
- 右图: {细节3——如有印花/Logo则展示印花微距，无则展示面料纱线纹理}，展示印花边缘清晰度/面料纱线编织微观结构。下方小字标注：{如PREMIUM FABRIC TEXTURE / VIBRANT PRINT}。

所有标注文字使用EightiesComeback Semi Bold Condensed字体，深灰色（#444444），字号小但清晰可读。三张图高度统一，间距均匀，整体居中排布。

整体要求：微距摄影质感、锐利清晰、面料纹理可见、缝线笔直精密、光影柔和自然。无模糊、无过度锐化、无噪点。

{通用负面prompt}
```

### 模块六：Lifestyle Scene Collage

**用途**: 多场景穿搭展示，激发购买欲望
**尺寸**: 16:9 横版（1464×824 Premium）/ 970×546（Basic）
**模块类型**: Premium Multi-Image / Standard Four Images

```
生成一张亚马逊A+男装T恤生活方式场景图，超宽横版画幅16:9，纯白背景，整体风格极简干净、留白充足，无阴影、无边框、无圆角、无任何UI组件与装饰元素。

画面顶部中央放置英文标题：{如EVERYDAY ESSENTIALS / YOUR NEW FAVORITE TEE}，EightiesComeback Semi Bold Condensed字体，纯黑色。

标题下方横向等距排列{4张}竖向实拍图，比例4:5，图片之间视觉均匀留白，整体居中排布。每张图模特不同（不同脸型、肤色、年龄25-40岁之间、不同体型），真实手机实拍摄影质感，画面边缘自然柔和。

4张场景（根据款式自动匹配适用场景）：

【场景A - 街头休闲 Everyday Street】
穿搭：T恤{颜色}+ 修身牛仔裤/休闲裤 + 运动鞋或帆布鞋
场景：城市街道/涂鸦墙/红砖墙前，生活化背景轻微虚化
构图：4:5竖屏，全身或三分之二全身
姿态：自然站立或走路抓拍，一手插袋，一手拿手机/咖啡
表情：放松自信，日常出门即视感
光线：上午10点自然光，色彩真实

【场景B - 户外/运动 Outdoor Active】
穿搭：T恤{其他颜色}+ 运动短裤/慢跑裤 + 跑鞋
场景：公园跑道/草坪/海边步道，自然光外景
构图：4:5竖屏，全身或半身动态拍摄
姿态：跑步中/拉伸/喝水等运动后放松姿态
表情：充满活力，自然微笑
光线：下午户外自然光，柔和不刺眼

【场景C - 居家/周末 Home Relaxed】
穿搭：T恤{浅色}+ 居家短裤/休闲长裤 + 拖鞋/赤脚
场景：明亮公寓客厅/阳台/窗边，背景有绿植、沙发、书籍
构图：4:5竖屏，坐姿或半卧姿态
姿态：坐着看书/喝咖啡/玩手机，最放松的状态
表情：柔和松弛，无刻意表情
光线：大面积窗光，柔和漫射

【场景D - 社交聚會 Social / Weekend】
穿搭：T恤{深色}+ 修身牛仔裤 + 皮靴/板鞋 + 手表
场景：氛围感餐厅/酒吧/城市夜景露台
构图：4:5竖屏，半身站立
姿态：手持饮品，身体微侧，轻松社交姿态
表情：自信微笑，眼神明亮
光线：暖色环境光+城市夜间光，轻微暖调

{通用负面prompt + 以下UGC风格规范：no supermodel, no editorial magazine style, no studio lighting, no plastic skin, no over-retouch, no stiff posed gesture, no mannequin hands, no extra/fused fingers, no distorted anatomy, no unrealistic body proportion, no influencer beauty filter, no fake empty scenery, no commercial advertising poster vibe, no 3D render look。衣物细节：subtle creases, natural fabric texture。人物细节：realistic male skin texture, natural stubble, minor skin imperfections。拍摄质感：iPhone camera quality, unfiltered, natural light。}
```

### 模块七：Size Chart

**用途**: 提供尺码表和测量方式说明，降低退货率
**尺寸**: 970 × 600 px
**模块类型**: Standard Image with Text

```
生成一张亚马逊A+男装T恤尺码指南图，横版画幅，背景为均匀纯色暖灰白（#F2F0EB），图片尺寸为970×600，极简商务风格。

画面采用左右分区：

左侧（约45%）：放置尺码数据表格——
- 标题：SIZE CHART，EightiesComeback Semi Bold Condensed字体，纯黑色
- 表格列：{Size, Chest, Shoulder, Length, Sleeve Length}
- 表格数据从{尺码数据}填充
- 风格极简：细线分隔、浅灰底色交替、Helvetica字体、深灰色
- 上方提示语：Tips: Please allow 0.4"-0.8" difference due to manual measurement.

右侧（约55%）：放置测量方式示意图——
- T恤线稿或实拍平面图
- 标注测量位置：
  · Chest（胸围）——腋下到腋下
  · Shoulder（肩宽）——肩缝到肩缝
  · Length（衣长）——后领中到衣摆
  · Sleeve Length（袖长）——肩缝到袖口
- 极简线条+文字标注，Helvetica字体，深灰色
- 下方小字：If not satisfied, please contact us directly.

{通用负面prompt}
```

---

## 输出格式模板

### 完整输出结构

```
# {品牌名} 男士{款式名}T恤 A+ Prompt 套件

## 商品信息摘要
| 项目 | 内容 |
|------|------|
| 品牌 | {Moikrakki} |
| 款式 | {款式名称} |
| 颜色 | {颜色列表} |
| 面料 | {面料成分} |
| 核心卖点 | {卖点1 · 卖点2 · 卖点3 · 卖点4} |
| 尺码范围 | {尺码范围} |

## 设计规范速查

### 颜色色板
| 用途 | 色值 |
|------|------|
| 背景主色 | #F2F0EB（暖灰白） |
| 深色对比背景 | #2C2C2C（深炭灰） |
| 标题文字 | #000000（纯黑） |
| 正文文字 | #333333 / #555555 / #888888 |
| 强调色 | #1A2744（海军蓝） |
| 产品颜色 | {颜色列表及色值，由用户提供} |

### 字体规格
| 用途 | 字体 | 大小参考 |
|------|------|---------|
| Logo | EightiesComeback Semi Bold Condensed | 画面高度 8-10% |
| 大标题 | EightiesComeback Semi Bold Condensed | 画面高度 18-20% |
| 副标题 | Helvetica Neue Light | 主标题 25-30% |
| 功能标签 | EightiesComeback Semi Bold Condensed | 画面高度 5-7% |
| 正文 | Helvetica Neue Light/Regular | 画面高度 3-4% |
| 表格/提示 | Helvetica Neue Light | 画面高度 2-3% |

---

### 模块搭配建议

**方案一：Premium A+（7模块，1464px）**
1. 模块一 Brand Hero Banner | 品牌认知
2. 模块二 Core Feature Highlights (Premium版) | 核心卖点
3. 模块三 Fabric & Material Close-up | 面料信任
4. 模块四 Comfort & Fit Scene | 穿着体验
5. 模块五 Craftsmanship Details | 工艺细节
6. 模块六 Lifestyle Scene Collage | 购买欲望
7. 模块七 Size Chart | 降低退货

**方案二：Basic A+（5模块，970px）**
1. 模块一 Brand Hero Banner (Basic版) | 品牌认知
2. 模块二 Core Feature Highlights (Basic版) | 核心卖点
3. 模块四 Comfort & Fit Scene | 穿着体验
4. 模块六 Lifestyle Scene Collage | 购买欲望
5. 模块七 Size Chart | 降低退货

---

### 模块内容

以上述 7 个模块模板为主体，每个模板输出完整的 prompt，所有 `{花括号}` 内容是用户可替换的部分。
```

---

## 使用说明

1. **直接输出** — 用户提供商品信息后，直接输出完整套件，不需要反问确认
2. **缺失信息用默认值** — 如果用户未提供某些信息（如具体颜色色值），使用合理默认值，并在 prompt 括号内标注 `[默认]`
3. **多颜色处理** — 如果用户提供多个颜色，在模块六（生活场景）中为不同场景分配不同颜色，在其他模块中统一使用用户指定的主色
4. **印花/图案处理** — 如果 T恤 有印花或 Logo，在模块一（右侧近景）、模块二（细节图）、模块五（第三细节图）中特别标注展示印花细节
5. **尺寸自适应** — 注意区分 Premium A+（1464px 宽）和 Basic A+（970px 宽），特别是在模块一、二、六中输出对应尺寸版本
6. **语言** — 分析说明用中文，prompt 正文用英文（直接给 GPT Image 用）
