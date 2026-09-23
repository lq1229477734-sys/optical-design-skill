# TechWiz LCD 3D 15 文本文件格式速查

TechWiz 文本文件使用 CRLF 换行和 UTF-8/ASCII；坐标与厚度在 `.str` 中用**米**，`.elt` 用 V，`.sdb` 用 s/V，`.stk` 厚度用 µm、角度用 deg。以下字段均来自 TechWiz LCD 3D v15 已打开或运行过的工程；其他版本应先用最小工程验证，不能直接假定兼容。

## .prj（VERSION 3）
```
MAIN {
  MaterialDB   "\Material_LC_Lens.db"        # 以 "\" 开头 = 相对工程目录
  SignalDB     "D:\path\to\<Name>\<Name>_Response.sdb"   # 响应工程用绝对路径
  StrFile      "\LAYOUT\<Name>.str"
  EltFile      "\INPUT\<Name>_xxx.elt"
  StkFile      "\<Name>_InputPolarizer.stk"
  LightSourceDB "\LightSource.ldb"
  LC 1  OPTICS 0 ...
}
LCCELL {
  Mesh_Length 1.5e-6   Mesh_Length_Max 3e-6
  BC-X 0  BC-Y 0                       # 0 = Periodic（已验证的取值）
  TimeFinal 1.0  TimeStep 1e-3  DataOutStep 1000     # 响应工程: 4.0 / 1e-3 / 10
  MaxSaturationTime 1e3  CriticalAngle 1e-3
  RUBBING { Field { "Name" "Top_Tilt" "Top_Twist" "Bottom_Tilt" "Bottom_Twist" "Layers" }
            Zones 7 { "LC_LENS" 2 90 2 90 16   # 其他非 LC 区域全 0 }
  }
}
OPTICS { WaveLength 550  NumTheta 10  NumPhi 36  SpecifyAngle 0 ... }
```
- Zones 表的名称 = .str 的 ZONE NAME，一一对应，否则 rubbing mismatch。
- 最稳妥的做法：复制已跑通的 `.prj`，只替换上述已验证字段。生成器会检查每个目标字段恰好出现一次，模板结构不匹配时退出。

## .str（VERSION 8，"Structure Definition Pro"）
```
STRUCTURE {
  COORDINATES 2 "X" "Y"
  NODES N        # 每个多边形 4 个节点，依次列出；最后 4 个是 SIMAREA
  1  -0.000100000000  -0.000005000000
  ...
  POLYGONS M
  POLYGON 4  1 2 3 4       # 多边形 1 = 整个单元（给底部公共电极）
  POLYGON 4  5 6 7 8       # 多边形 2.. = 各条顶部电极
  SIMAREA 4  ...
}
LOCAL { LOCNODES 8 ... LOCPOLYGONS 2 (上/下两个整面局部区域，CONDITION {} 空) }
ZONE { NAME "TOP_GLASS" MATERIAL "GLASS" MAT_TYPE "INSULATOR" THICKNESS 5e-06 PLANAR 1 DOP 1.00
       MULTI_LAYER 1 SUBSTRATE "SUB" MASK_TYPE 0 MASK 0 GAP_POSITION 0 0 }
ZONE { NAME "TOP_SEG_ITO" MATERIAL "ITO" MAT_TYPE "METAL" THICKNESS 5e-08 ... TAPER_TYPE 1 TAPER_ANGLE 90 TAPER_ROUND 2
       MASK 6 2 3 4 5 6 7 }          # MASK <个数> <多边形编号...>
ZONE { NAME "TOP_PI" ... }
ZONE { NAME "LC_LENS" MATERIAL "LC-LENS-DN030" MAT_TYPE "LC" THICKNESS 2.5e-05 SUBSTRATE "FILL" HARDENING 0
       MASK 0  LOCMASK_TOP 1 2  LOCMASK_BOT 1 1 }
ZONE { NAME "BOT_PI" ... }  ZONE { NAME "BOT_COM_ITO" ... MASK 1 1 }  ZONE { NAME "BOT_GLASS" ... SUBSTRATE "SUB" }
ELECTRODE { NAME "BOT_COM" POLYGON 1 1 }
ELECTRODE { NAME "E1_EDGE" POLYGON 2 2 3 }     # 同一电极的多个多边形 → 同电位
```
- ZONE 顺序：**从上到下**（TOP_GLASS 在前）。
- 周期边界电极：中心在 ±pitch/2 的条被裁成两个半条（x∈[−p/2, −p/2+w/2] 与 [p/2−w/2, p/2]），属于同一 ELECTRODE。

## .elt（VERSION 5）
```
ELECTRODES {
  FIELD { "ID" "Name" "Function" "Link" "Voltage Type" "Voltage" "Signal" "Start" "Stop" "Step" "Main/Sub" }
  ELECTRODE 4 {
    1 "BOT_COM" NA 0 DC                0.0 0 0.0 0.0  0.0 Sub
    2 "E1_EDGE" NA 0 SWEEP(SATURATION) 0.0 0 0.0 11.0 1.0 Main
    3 "E2_MID"  NA 0 DC                2.0 0 0.0 0.0  0.0 Sub
    4 "E3_CEN"  NA 0 DC                1.0 0 0.0 0.0  0.0 Sub
  }
}
```
- 电压类型：`DC` / `SWEEP(SATURATION)` / `SIGNAL`（波形在 .sdb，GUI 里选 Signal 名）。
- 恰好一个 `Main`（被扫描或加信号的电极）。
- 老写法（`0 "BOT_COMMON" COMMON 0 DC ...` 无 ELECTRODE n 块）是早期离线生成的，TechWiz 15 常拒绝；以上格式是 GUI "Save as... Electrode Information File" 的原生输出。

## .stk（VERSION 2，光学堆栈，从上到下）
```
"Name" "ID" "Thickness" "Theta" "Phi" "Psi" "Trans-Absorp" "Material ID"
  "LC_Cell"   1  0    0 0 0  1 1
  "Polarizer" 2  200  0 0 0  0 3000      # Phi = 吸收轴！Phi=0 → 透过轴 90°(Y)
```
- 单偏振片（入光侧、LC 下方）：用于透镜 e 光。
- TN 透过率：`Polarizer(Phi 90) / LC_Cell / Polarizer(Phi 0)`。

## .sdb（Signal DB）
```
Version 1
"Signal database for TechWiz LCD"
{ Data { "LENS_STEP" {
    Time 0.0    Volt 0     Time 0.010 Volt 0
    Time 0.011  Volt 11    Time 1.000 Volt 11
    Time 1.001  Volt 0     Time 4.000 Volt 0 } } }
```
阶跃用短斜坡而非同一时刻的瞬时跳变。示例采用 1 ms；具体斜坡和输出采样必须足以分辨目标响应时间。

## Material.db（Version 3）
Data 行字段顺序：`"Name" Index Type Chirality Refractive Biaxial K11 K22 K33 EpsPar EpsPer Pitch Gamma1 Gamma2 A1..A6 Density Pol NeXr NeXi NoYr NoYi NoZr NoZi Resistivity Theta Phi Red Green Blue Reflectance`
- 新液晶：从同一份材料库复制与目标模型相符的 `"LC"` 或 `"LC-TN"` 行，改名并使用该库中未占用的 Index；无手性/无限螺距模型才设置 `Chirality=0`、`Pitch=0`，并核对 `NeXr`、`NoYr` 及弹性/介电/黏度参数。
- 还要复制对应的 `Additional_Data` 块（按名称出现第二次的位置），把块名改成新名。
- 示例工作区已有自定义材料：`LC-LENS-DN010`（ne 1.60/no 1.50）、`LC-LENS-DN030`（ne 1.77/no 1.47），其余参数同该工作区的 `"LC"`：K11/K22/K33 = 10.87/9.5/15.37 pN，ε∥/ε⊥ = 9.3/4.0，γ1 = 0.1 Pa·s。不要假设其他材料库也含这些条目或 Index。
- Polarizer = Index 3000（Type 5，NeXi 1.5e-3 → Ne 方向吸收）。

## 输出
- `LC/<proj>_MESH.dat`、`LC/<proj>_ELECTRODE.dat`、`LC/<proj>_dat/*<V>[V]_<t>[ms].dat`（Signal 工程只有 `[ms]`）
- `MESH/<proj>_Volume of Each Zone.txt`、`MESH/*_CHECK-*.str`（网格检查）
- `OPTICS/*.pol`（角度透过率）、`*_br.pol`（亮度，需 LightSource）、`*_Trans-Time_Signal.grp`（时间-透过率）
- `<proj>.log`：进度与报错，首先看它。

二进制后处理器会检查文件头、节点数、最低字节长度和非有限数值。格式仍是 v15 工程的经验解析结果：MESH 从第 6 字节读取 little-endian `int32` 节点数，第 14 字节起每节点 56 B；director 文件头 24 B，之后每节点 7 个 little-endian `float32`。若 TechWiz 版本或文件长度不符，应停止并重新确认格式，不能通过截断或补零强行解析。
