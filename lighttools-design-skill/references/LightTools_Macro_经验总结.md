# LightTools Macro 经验总结与可复用模板

> 适用场景：LightTools 中对几何尺寸、表面 2D Pattern、厚度/长度、接收器角度亮度图进行自动扫描、仿真和 TXT 导出。  
> 经验来源：LightTools MACRO Reference Guide、Core User Guide，以及我们反复调试过的 `colli1_lc`、`colli1_lc_1`、`colli1_lc_2`、`colli1_11`、`Cube_2` 等模型扫描宏。

---

## 1. Macro 的核心理解

LightTools Macro 本质上是：

```text
BASIC 解释器 + LightTools 命令解释器 + LightTools 数据库访问函数
```

因此写宏时要分清三类操作：

| 类型 | 典型命令/函数 | 用途 |
|---|---|---|
| BASIC 控制 | `FOR / NEXT`, `WHILE / WEND`, `IF THEN`, `PRINT`, `SYSTEM` | 循环、判断、输出、调用 Windows 命令 |
| LightTools 命令 | `LTCMD("Fit")`, `LTCMD("BeginAllSimulations")`, `LTCMD("Export ...")` | 执行 LightTools 界面命令 |
| 数据库访问 | `LTDBLIST$`, `LTLISTBYNAME$`, `LTLISTNEXT$`, `LTDBGET`, `LTDBSET`, `LTDBKEYSTR$` | 查找对象、读取/修改参数 |

我实际生成宏时，最重要的原则是：**尽量不要依赖鼠标选择，而是通过对象名和数据库 key 精确定位对象。**

---

## 2. 一个稳定 Macro 的标准结构

推荐所有扫描宏都按下面结构写：

```basic
ECHO OFF
LTBSET UPDATE 1
LTBSET DIALOG 0

REM ========== 用户参数区 ==========
OUTDIR$ = "D:\tcl mars\lighttools\tunbale privacy\skem final\1"
UNIT_SCALE = 0.001
TARGET_SOLID_NAME$ = "colli1_11"
TARGET_RECEIVER_NAME$ = "BLUReceiver"
GEOM_FIELD$ = "LENGTH"
VIEW3D$ = "\V3D"
CHART_VIEW_CMD$ = "\VChart_BLUReceiver_正向_角度_亮度"
CHART_SELECT_CMD$ = ""
DQ$ = CHR$(34)

REM ========== 创建输出文件夹 ==========
MkDirCmd$ = "cmd /c if not exist " + DQ$ + OUTDIR$ + DQ$ + " mkdir " + DQ$ + OUTDIR$ + DQ$
SYSTEM MkDirCmd$

REM ========== 查找对象 ==========
REM 这里查 solid / primitive / surface / receiver

REM ========== 扫描循环 ==========
FOR idx = 1 TO 10
    REM 设置参数
    REM Fit
    REM BeginAllSimulations
    REM 切换 chart
    REM Export
NEXT idx

LTBSET UPDATE 1
LTBSET DIALOG 1
PRINT "Sweep finished."
END
```

### 为什么这样写？

1. `ECHO OFF`：减少控制台输出，避免宏运行时刷屏。
2. `LTBSET DIALOG 0`：避免弹出窗口阻断自动运行。
3. `DQ$ = CHR$(34)`：处理 Windows 路径中的空格，生成带双引号的命令。
4. 每次导出前先 `del` 旧文件，避免 LightTools 自动生成 `.1.txt`、`.2.txt` 后文件名混乱。
5. 结尾一定恢复：

```basic
LTBSET UPDATE 1
LTBSET DIALOG 1
```

否则后续手动操作可能出现界面不刷新或对话框不显示的问题。

---

## 3. 单位换算经验

你现在的大多数模型单位是 **mm**，而扫描需求通常用 **um** 表示。

```text
1 um = 0.001 mm
10 um = 0.01 mm
100 um = 0.1 mm
```

所以宏中建议统一写：

```basic
UNIT_SCALE = 0.001
L_um = idx * 10
L_model = L_um * UNIT_SCALE
```

不要直接把 `10` 写进 `LTDBSET`，否则 LightTools 会理解成 `10 mm`，尺寸会放大 1000 倍。

---

## 4. 对象定位的通用方法

### 4.1 查找 Solid

```basic
SolidList$ = LTDBLIST$("COMPONENTS[1]", "SOLID")
TargetSolidKey$ = LTLISTBYNAME$(SolidList$, TARGET_SOLID_NAME$)

IF TargetSolidKey$ = "" THEN
    PRINT "ERROR: Cannot find solid named "; TARGET_SOLID_NAME$
    LTBSET DIALOG 1
    END
END IF
```

常用对象名：

```text
colli1_11
colli1_lc
colli1_lc_1
colli1_lc_2
Cube_2
```

### 4.2 查找 Primitive

如果是立方体，优先用 `CUBE_PRIMITIVE`：

```basic
PrimList$ = LTDBLIST$(TargetSolidKey$, "CUBE_PRIMITIVE")
TargetPrimKey$ = LTLISTNEXT$(PrimList$)

IF TargetPrimKey$ = "" THEN
    PrimList2$ = LTDBLIST$(TargetSolidKey$, "PRIMITIVE")
    TargetPrimKey$ = LTLISTNEXT$(PrimList2$)
END IF

IF TargetPrimKey$ = "" THEN
    PRINT "ERROR: Cannot find primitive under "; TARGET_SOLID_NAME$
    LTBSET DIALOG 1
    END
END IF
```

这个 fallback 很重要，因为有些模型里对象显示为 CubePrimitive，但数据库过滤器不一定每次都完全一致。

### 4.3 查找 Surface

```basic
SurfList$ = LTDBLIST$(TargetPrimKey$, "PLANAR_SURFACE")
LeftSurfKey$ = LTLISTBYNAME$(SurfList$, "LeftSurface")

SurfList2$ = LTDBLIST$(TargetPrimKey$, "PLANAR_SURFACE")
RightSurfKey$ = LTLISTBYNAME$(SurfList2$, "RightSurface")
```

注意：同一个 list 遍历后游标会移动，所以查 `LeftSurface` 和 `RightSurface` 时最好重新生成一次 `SurfList$`。

### 4.4 查找 2D Pattern 的 RectangleElement

对于 `2D_Pattern / RectangleElement / X_Width`，常用过滤器是：

```basic
RectList$ = LTDBLIST$(SurfaceKey$, "RECTANGLE_UNIT_CELL")
RectKey$ = LTLISTNEXT$(RectList$)

WHILE RectKey$ <> ""
    OldValue = LTDBGET(RectKey$, "X_Width")
    SetStatus = LTDBSET(RectKey$, "X_Width", WidthModel)
    RectKey$ = LTLISTNEXT$(RectList$)
WEND
```

如果直接从全局找，也可以这样：

```basic
RectList$ = LTDBLIST$("COMPONENTS[1]", "RECTANGLE_UNIT_CELL")
RectKey$ = LTLISTNEXT$(RectList$)

WHILE RectKey$ <> ""
    KeyStr$ = LTDBKEYSTR$(RectKey$)

    hitSolid = INSTR(KeyStr$, "colli1_lc")
    hitLeft = INSTR(KeyStr$, "LeftSurface")
    hitRight = INSTR(KeyStr$, "RightSurface")

    IF hitSolid > 0 AND (hitLeft > 0 OR hitRight > 0) THEN
        SetStatus = LTDBSET(RectKey$, "X_Width", WidthModel)
    END IF

    RectKey$ = LTLISTNEXT$(RectList$)
WEND
```

这种方法适合对象层级不确定时，通过 `LTDBKEYSTR$` 字符串筛选。

---

## 5. 修改长度、厚度、X_Width 的方法

### 5.1 修改立方体长度 LENGTH

```basic
SetStatus = LTDBSET(TargetPrimKey$, "LENGTH", L_model)

IF SetStatus <> 0 THEN
    PRINT "ERROR: LTDBSET failed. Status = "; SetStatus
ELSE
    PRINT "Changed LENGTH to "; L_model
END IF
```

常见写法：

```basic
GEOM_FIELD$ = "LENGTH"
SetStatus = LTDBSET(TargetPrimKey$, GEOM_FIELD$, L_model)
```

这样以后把 `LENGTH` 改成别的字段更方便。

### 5.2 修改 2D Pattern 的 X_Width

```basic
SetStatus = LTDBSET(RectKey$, "X_Width", WidthModel)
```

经验：

- `X_Width` 一般作用在 `RECTANGLE_UNIT_CELL` 上。
- 不是作用在 `PLANAR_SURFACE` 上。
- 如果报错或没有变化，先 `PRINT LTDBKEYSTR$(RectKey$)` 确认是否找到了真正的 RectangleElement。

---

## 6. 单参数扫描模板：扫描 colli1_11 的 LENGTH

```basic
REM Sweep colli1_11 LENGTH: 10 um to 100 um, step 10 um

ECHO OFF
LTBSET UPDATE 1
LTBSET DIALOG 0

OUTDIR$ = "D:\tcl mars\lighttools\tunbale privacy\skem final\1"
UNIT_SCALE = 0.001
GEOM_FIELD$ = "LENGTH"
TARGET_SOLID_NAME$ = "colli1_11"
TARGET_RECEIVER_NAME$ = "BLUReceiver"
VIEW3D$ = "\V3D"
CHART_VIEW_CMD$ = "\VChart_BLUReceiver_正向_角度_亮度"
CHART_SELECT_CMD$ = ""
DQ$ = CHR$(34)

MkDirCmd$ = "cmd /c if not exist " + DQ$ + OUTDIR$ + DQ$ + " mkdir " + DQ$ + OUTDIR$ + DQ$
SYSTEM MkDirCmd$

SolidList$ = LTDBLIST$("COMPONENTS[1]", "SOLID")
TargetSolidKey$ = LTLISTBYNAME$(SolidList$, TARGET_SOLID_NAME$)

IF TargetSolidKey$ = "" THEN
    PRINT "ERROR: Cannot find solid named "; TARGET_SOLID_NAME$
    LTBSET DIALOG 1
    END
END IF

PrimList$ = LTDBLIST$(TargetSolidKey$, "CUBE_PRIMITIVE")
TargetPrimKey$ = LTLISTNEXT$(PrimList$)

IF TargetPrimKey$ = "" THEN
    PrimList2$ = LTDBLIST$(TargetSolidKey$, "PRIMITIVE")
    TargetPrimKey$ = LTLISTNEXT$(PrimList2$)
END IF

IF TargetPrimKey$ = "" THEN
    PRINT "ERROR: Cannot find primitive under "; TARGET_SOLID_NAME$
    LTBSET DIALOG 1
    END
END IF

FOR idx = 1 TO 10

    L_um = idx * 10
    L_model = L_um * UNIT_SCALE
    Label$ = STR$(L_um)

    SetStatus = LTDBSET(TargetPrimKey$, GEOM_FIELD$, L_model)

    IF SetStatus <> 0 THEN
        PRINT "ERROR: LTDBSET failed at "; Label$; " um. Status="; SetStatus
    ELSE
        PRINT TARGET_SOLID_NAME$; " LENGTH = "; Label$; " um"

        CmdStatus = LTCMD(VIEW3D$)
        CmdStatus = LTCMD("Fit")
        CmdStatus = LTCMD("BeginAllSimulations")

        CmdStatus = LTCMD(CHART_VIEW_CMD$)
        IF CmdStatus <> 0 THEN
            PRINT "WARNING: Could not switch to chart window."
            PRINT "Replace CHART_VIEW_CMD$ with exact command from .ltr recover file."
        END IF

        IF CHART_SELECT_CMD$ <> "" THEN
            CmdStatus = LTCMD(CHART_SELECT_CMD$)
        END IF

        OutBase$ = OUTDIR$ + "\" + Label$ + "um"

        DelCmd$ = "cmd /c del /q " + DQ$ + OutBase$ + "*.txt" + DQ$
        SYSTEM DelCmd$

        CmdStatus = LTCMD("Export " + LTSTR$(OutBase$))

        RenCmd$ = "cmd /c if exist " + DQ$ + OutBase$ + ".1.txt" + DQ$ + " ren "
        RenCmd$ = RenCmd$ + DQ$ + OutBase$ + ".1.txt" + DQ$ + " " + DQ$ + Label$ + "um.txt" + DQ$
        SYSTEM RenCmd$

        PRINT "Export requested: "; OutBase$; ".txt"
    END IF

NEXT idx

LTBSET UPDATE 1
LTBSET DIALOG 1
PRINT "LENGTH sweep finished."
END
```

---

## 7. 双参数扫描模板：两个立方体厚度/长度嵌套扫描

典型需求：

```text
colli1_lc_2 LENGTH: 100-150 um, step 10 um
colli1_lc_1 LENGTH: 10-100 um, step 10 um
输出文件名：100um-10um.txt, 100um-20um.txt, ...
```

核心结构：

```basic
FOR idx2 = 10 TO 15

    L2_um = idx2 * 10
    L2_model = L2_um * UNIT_SCALE
    Label2$ = STR$(L2_um)

    SetStatus2 = LTDBSET(Prim2Key$, "LENGTH", L2_model)

    IF SetStatus2 = 0 THEN

        FOR idx1 = 1 TO 10

            L1_um = idx1 * 10
            L1_model = L1_um * UNIT_SCALE
            Label1$ = STR$(L1_um)

            SetStatus1 = LTDBSET(Prim1Key$, "LENGTH", L1_model)

            IF SetStatus1 = 0 THEN
                CmdStatus = LTCMD("\V3D")
                CmdStatus = LTCMD("Fit")
                CmdStatus = LTCMD("BeginAllSimulations")
                CmdStatus = LTCMD(CHART_VIEW_CMD$)

                OutBase$ = OUTDIR$ + "\" + Label2$ + "um-" + Label1$ + "um"
                CmdStatus = LTCMD("Export " + LTSTR$(OutBase$))
            END IF

        NEXT idx1

    END IF

NEXT idx2
```

经验：

- 外层参数通常放“变化较慢”的参数。
- 文件名顺序建议与循环顺序一致：`外层-内层.txt`。
- 后续 Python 处理时更容易从文件名解析参数。

---

## 8. X_Width + 厚度联合扫描模板

典型需求：

```text
外层：X_Width = 30, 40, 50, 60 um
内层：colli1_lc_2 LENGTH = 100-150 um
再内层：colli1_lc_1 LENGTH = 10-100 um
输出文件夹：
xwidth_30um\100um-10um.txt
xwidth_40um\100um-10um.txt
...
```

推荐文件夹结构：

```text
xwidth_thickness_sweep
├── xwidth_30um
│   ├── 100um-10um.txt
│   ├── 100um-20um.txt
│   └── ...
├── xwidth_40um
├── xwidth_50um
└── xwidth_60um
```

核心逻辑：

```basic
FOR idxW = 3 TO 6

    WidthUm = idxW * 10
    WidthModel = WidthUm * UnitScale
    WLabel$ = STR$(WidthUm)

    XDir$ = OutRoot$ + "\xwidth_" + WLabel$ + "um"
    MkXDirCmd$ = "cmd /c if not exist " + DQ$ + XDir$ + DQ$ + " mkdir " + DQ$ + XDir$ + DQ$
    SYSTEM MkXDirCmd$

    REM 修改多个表面的 X_Width
    CALL SetRectWidthOnSurface(Surf1LeftKey$, WidthModel)
    CALL SetRectWidthOnSurface(Surf1RightKey$, WidthModel)
    CALL SetRectWidthOnSurface(Surf2RightKey$, WidthModel)

    REM 再做双厚度扫描
    FOR idx2 = 10 TO 15
        FOR idx1 = 1 TO 10
            REM 设置 LENGTH、仿真、导出
        NEXT idx1
    NEXT idx2

NEXT idxW
```

注意：LightTools Macro 的子程序写法与普通 BASIC 类似，但实际调试中，为了减少兼容问题，我通常会直接展开代码，而不是过度封装成 `SUB`。

---

## 9. 图表导出的关键经验

### 9.1 角度亮度图最好手动打开一次

在运行导出宏之前，建议先在 LightTools 中手动打开目标图：

```text
Analysis > Angular Luminance Display > LumViewer for BLUReceiver
```

然后宏里切换到已有图表：

```basic
CHART_VIEW_CMD$ = "\VChart_BLUReceiver_正向_角度_亮度"
CmdStatus = LTCMD(CHART_VIEW_CMD$)
```

如果失败，说明图表窗口名不一致，需要从 `.ltr` 或 recover/log 文件里复制准确命令。

常见图表命令形式：

```text
\VChart_BLUReceiver_正向_角度_亮度
\VChart_Receiver_4_正向_角度_亮度
```

### 9.2 Export 导出的是“当前激活图表”

这点非常关键：

```basic
CmdStatus = LTCMD("Export " + LTSTR$(OutBase$))
```

这条命令不会自动知道你想导出哪个接收器，它导出的是当前激活的 chart。因此：

1. 先 `BeginAllSimulations`
2. 再切到目标 angular luminance chart
3. 再 `Export`

顺序不能乱。

### 9.3 文件名 `.1.txt` 的处理

LightTools 可能会自动导出为：

```text
10um.1.txt
100um-10um.1.txt
```

因此导出后建议重命名：

```basic
RenCmd$ = "cmd /c if exist " + DQ$ + OutBase$ + ".1.txt" + DQ$ + " ren "
RenCmd$ = RenCmd$ + DQ$ + OutBase$ + ".1.txt" + DQ$ + " " + DQ$ + Label$ + "um.txt" + DQ$
SYSTEM RenCmd$
```

双参数文件名：

```basic
OldFile$ = OutBase$ + ".1.txt"
NewFile$ = Label2$ + "um-" + Label1$ + "um.txt"
RenCmd$ = "cmd /c if exist " + DQ$ + OldFile$ + DQ$ + " ren " + DQ$ + OldFile$ + DQ$ + " " + DQ$ + NewFile$ + DQ$
SYSTEM RenCmd$
```

---

## 10. Windows 文件夹和路径处理

### 10.1 创建文件夹

```basic
DQ$ = CHR$(34)
MkDirCmd$ = "cmd /c if not exist " + DQ$ + OUTDIR$ + DQ$ + " mkdir " + DQ$ + OUTDIR$ + DQ$
SYSTEM MkDirCmd$
```

### 10.2 删除旧结果

```basic
DelCmd$ = "cmd /c del /q " + DQ$ + OutBase$ + "*.txt" + DQ$
SYSTEM DelCmd$
```

### 10.3 为什么一定要加双引号？

你的路径里经常有空格，例如：

```text
D:\tcl mars\lighttools\tunbale privacy\skem final
```

如果没有双引号，Windows 会把它拆成多个参数，导致 `mkdir`、`del`、`ren` 失败。

---

## 11. 常见报错和处理方法

### 11.1 `Unknown variable "LumViewLuminanceChart"`

原因：直接写了一个不存在的变量或对象名，LightTools 并没有把它识别为图表对象。

解决：不要直接假设 chart 变量存在，而是：

```basic
CmdStatus = LTCMD(CHART_VIEW_CMD$)
CmdStatus = LTCMD("Export " + LTSTR$(OutBase$))
```

并且从 recover/log 文件中复制真实 chart view 命令。

---

### 11.2 找不到输出 txt 文件

可能原因：

1. 图表没有激活，`Export` 导出失败。
2. 输出到了 `.1.txt`，但你在找 `.txt`。
3. 文件夹路径有空格，`mkdir` 或 `Export` 路径没处理好。
4. LightTools 当前激活的是 3D 视图，不是角度亮度图。

建议加入这些输出：

```basic
PRINT "Output folder = "; OUTDIR$
PRINT "Chart command = "; CHART_VIEW_CMD$
PRINT "OutBase = "; OutBase$
PRINT "Export status = "; CmdStatus
```

---

### 11.3 `LTDBSET failed`

常见原因：

1. key 找错了，比如把 `SOLID` key 当成 `PRIMITIVE` key。
2. 字段名写错，比如 `Length`、`length`、`LENGTH` 混淆。
3. 该对象不支持这个字段。
4. 单位值不合理，几何体出错。

调试方法：

```basic
PRINT "Target key = "; TargetPrimKey$
PRINT "Target key string = "; LTDBKEYSTR$(TargetPrimKey$)
OldValue = LTDBGET(TargetPrimKey$, "LENGTH")
PRINT "Old LENGTH = "; OldValue
```

---

### 11.4 没有任何 RectangleElement 被修改

宏中加入计数：

```basic
changedCount = 0
checkedCount = 0

REM 每找到一个对象 checkedCount + 1
REM 每成功修改一次 changedCount + 1

PRINT "Checked RECTANGLE_UNIT_CELL count = "; checkedCount
PRINT "Changed RECTANGLE_UNIT_CELL count = "; changedCount

IF changedCount = 0 THEN
    PRINT "WARNING: No RectangleElement was changed."
END IF
```

如果 `checkedCount` 也为 0，说明过滤器或搜索根节点错了。  
如果 `checkedCount > 0` 但 `changedCount = 0`，说明筛选条件中的 solid/surface 字符串不匹配。

---

## 12. 推荐调试顺序

写复杂宏时，不要一开始就跑完整扫描。推荐顺序：

1. 只查找对象，打印 key。
2. 只修改一个参数，不仿真。
3. 修改一个参数后 `Fit`，手动检查模型是否变化。
4. 只跑一次仿真。
5. 只导出一次 txt。
6. 再扩大到单循环。
7. 最后再写双循环或三循环。

实际最容易出问题的是：

```text
对象 key 找错 > chart 没激活 > 文件名/路径问题 > 单位换算问题
```

---

## 13. 我的宏生成习惯

### 13.1 尽量把用户可改参数放在开头

```basic
OUTDIR$ = "..."
UNIT_SCALE = 0.001
TARGET_SOLID_NAME$ = "colli1_11"
TARGET_RECEIVER_NAME$ = "BLUReceiver"
CHART_VIEW_CMD$ = "\VChart_BLUReceiver_正向_角度_亮度"
```

这样你后续只需要改开头区域，不容易误改主体逻辑。

### 13.2 每一步都打印关键信息

```basic
PRINT "Target solid key = "; TargetSolidKey$
PRINT "Target primitive key = "; TargetPrimKey$
PRINT "Sweep field = "; GEOM_FIELD$
PRINT "Output folder = "; OUTDIR$
```

这比宏短一点但不打印信息更可靠，因为 LightTools 宏出错时不容易定位。

### 13.3 对关键对象先检查是否为空

```basic
IF TargetSolidKey$ = "" THEN
    PRINT "ERROR: Cannot find solid."
    LTBSET DIALOG 1
    END
END IF
```

不要让宏在 key 为空时继续跑，否则后面报错会更难看懂。

### 13.4 避免写太长的一行

LightTools Macro 单行长度有限，长的 Windows 命令建议拆成多行拼接：

```basic
RenCmd$ = "cmd /c if exist " + DQ$ + OldFile$ + DQ$ + " ren "
RenCmd$ = RenCmd$ + DQ$ + OldFile$ + DQ$ + " " + DQ$ + NewFile$ + DQ$
SYSTEM RenCmd$
```

---

## 14. 常用代码片段库

### 14.1 从 idx 生成 Label

最稳妥的写法是手动映射：

```basic
IF idx = 1 THEN Label$ = "10"
IF idx = 2 THEN Label$ = "20"
IF idx = 3 THEN Label$ = "30"
IF idx = 4 THEN Label$ = "40"
IF idx = 5 THEN Label$ = "50"
IF idx = 6 THEN Label$ = "60"
IF idx = 7 THEN Label$ = "70"
IF idx = 8 THEN Label$ = "80"
IF idx = 9 THEN Label$ = "90"
IF idx = 10 THEN Label$ = "100"
```

也可以用：

```basic
Label$ = STR$(idx * 10)
```

但某些 BASIC 环境里 `STR$` 可能带空格，文件名可能变成异常格式，所以在关键文件名中我更偏向手动映射。

### 14.2 切换 3D 视图并 Fit

```basic
CmdStatus = LTCMD("\V3D")
CmdStatus = LTCMD("Fit")
```

### 14.3 开始所有仿真

```basic
CmdStatus = LTCMD("BeginAllSimulations")
```

### 14.4 导出当前激活图表

```basic
OutBase$ = OUTDIR$ + "\" + Label$ + "um"
CmdStatus = LTCMD("Export " + LTSTR$(OutBase$))
```

### 14.5 查找 Receiver

```basic
ReceiverList$ = LTDBLIST$("COMPONENTS[1]", "RECEIVER")
ReceiverKey$ = LTLISTBYNAME$(ReceiverList$, "BLUReceiver")

IF ReceiverKey$ = "" THEN
    PRINT "WARNING: Cannot find receiver named BLUReceiver"
ELSE
    PRINT "Receiver key = "; ReceiverKey$
END IF
```

---

## 15. 生成新宏时我需要的信息

如果以后要让我快速生成一个新 LightTools 扫描宏，最好一次给出下面信息：

```text
1. 要扫描的对象名：例如 colli1_11 / colli1_lc_1 / colli1_lc_2
2. 要扫描的字段：LENGTH / X_Width / 其他字段
3. 如果是 2D Pattern：在哪个 Surface，LeftSurface 还是 RightSurface
4. 扫描范围：起点、终点、步长，单位 um 还是 mm
5. 模型单位：通常是 mm
6. 接收器名字：例如 BLUReceiver
7. 要导出的图：角度亮度图 / 照度图 / 其他图
8. 输出文件夹路径
9. 文件命名规则：例如 10um.txt 或 100um-10um.txt
10. 是否需要新建子文件夹
```

示例需求：

```text
扫描 colli1_lc_1 的 LeftSurface 下 2D_Pattern 的 RectangleElement 的 X_Width，
从 10 um 到 25 um，步长 5 um；
每个 X_Width 下再扫描 colli1_lc_1 的 LENGTH 从 10 um 到 100 um，步长 10 um；
接收器是 BLUReceiver，导出角度亮度 txt；
输出到 D:\tcl mars\lighttools\tunbale privacy\skem final\scan。
```

---

## 16. 最推荐的稳定宏策略

对于你的 LightTools 扫描任务，我目前最推荐以下策略：

1. **几何参数用 `LTDBSET` 直接改数据库。**  
   比用界面命令更稳定。

2. **对象定位用名称 + key。**  
   不要依赖当前选择对象。

3. **2D Pattern 用 `RECTANGLE_UNIT_CELL` 找。**  
   需要时配合 `LTDBKEYSTR$` 判断 solid/surface 名称。

4. **角度亮度导出前手动打开 chart 一次。**  
   宏只负责切换已有 chart 并导出。

5. **所有路径都加双引号。**  
   你的路径含空格，不加双引号会经常失败。

6. **导出前删除旧结果，导出后处理 `.1.txt`。**  
   保证后处理程序能稳定读取固定文件名。

7. **复杂扫描建立子文件夹。**  
   例如 `xwidth_20um`、`xwidth_25um`，方便后续 Python/Matlab 分析。

---

## 17. 常见任务对应模板

| 任务 | 推荐模板 |
|---|---|
| 单个立方体长度扫描 | 第 6 节 |
| 两个立方体厚度/长度嵌套扫描 | 第 7 节 |
| 同时修改左右表面 X_Width | 第 4.4 节 + 第 5.2 节 |
| 三个表面 X_Width 同步扫描 | 第 8 节的外层 X_Width 修改部分 |
| X_Width + 双厚度联合扫描 | 第 8 节 |
| 导出角度亮度矩阵 | 第 9 节 |
| 文件名固定为 `10um.txt` | 第 9.3 节 |

---

## 18. 最后总结

LightTools Macro 的关键不是语法复杂，而是对象定位和导出流程容易出错。实际最稳的宏通常具备下面特征：

```text
参数集中在开头
对象 key 明确打印
每次设置参数后检查状态
仿真前 Fit
导出前切换 chart
路径全部加引号
导出后重命名文件
最后恢复 DIALOG 和 UPDATE
```

只要按照这个框架，后续无论是扫描 `LENGTH`、`X_Width`、双厚度、三表面同步变化，还是生成分层文件夹，都可以在同一套结构上快速改出来。
