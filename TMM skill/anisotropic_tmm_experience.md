# 各向同性 / 各向异性传输矩阵计算成功经验总结

适用对象：DBR、多层膜、各向异性薄膜、液晶层、旋转光轴结构、s/p 反射透射、角度-波长赝色图，以及使用 `pyllama` 或自写 4×4 Berreman / scattering matrix 程序的任务。

---

## 1. 总体判断：什么时候用 2×2，什么时候用 4×4

### 1.1 各向同性多层膜

如果所有层都是各向同性材料，即

```text
nx = ny = nz = n
ε = diag(n², n², n²)
```

且没有偏振耦合，那么可以使用传统 2×2 TMM。此时 s 光和 p 光彼此独立，只需要分别计算：

- s 光：电场垂直入射面；
- p 光：电场在入射面内；
- 每层相位厚度为 `δ = k0 * n * d * cosθ_layer`；
- 通过 Snell 定律求每层角度。

这种方法速度快、稳定，适合普通 DBR、AR 膜、均匀介质膜堆。

### 1.2 各向异性多层膜

如果任意一层满足

```text
nx ≠ ny 或 ny ≠ nz 或 存在旋转光轴
```

就应该优先使用 4×4 Berreman 方法。原因是：

- s/p 不一定独立；
- 层内本征波不再简单等于 s、p；
- 光轴旋转会引入交叉偏振项，例如 `R_s_to_p`、`T_p_to_s`；
- 传统 2×2 方法只能处理特殊情形，比如光轴正好沿主轴且无耦合。

### 1.3 液晶、扭曲层、连续变化光轴

如果光轴沿 z 方向变化，例如 TN 液晶、螺旋胆甾相、逐层旋转双折射膜，应把连续结构切成很多薄层，每一层近似均匀，再对每一层建立 4×4 矩阵。

经验上：

```text
每层相位变化不要太大；
旋转角每层不要太大；
先用 50 层、100 层、200 层做收敛性检查。
```

---

## 2. 坐标系和偏振定义必须先固定

很多错误不是公式错，而是坐标系错。

推荐固定如下定义：

```text
z：膜层法线方向，光从 entry 向 exit 沿 +z 传播
x-z：入射面
x：切向波矢方向
 y：垂直入射面方向
```

因此：

```text
s 光：E 沿 y 方向
p 光：E 在 x-z 平面内
Kx = n_entry * sin(theta_in)
Ky = 0
```

如果你说“x 方向是 s 光方向”，那么等价于把入射面换成 y-z 平面。此时不能直接套用默认 `Kx` 形式，需要重新定义切向波矢方向，或者把结构坐标整体旋转，使程序内部仍然保持“s 光沿 y”的约定。

最稳妥做法：

```text
程序内部永远保持：入射面 = x-z，s = y。
如果物理问题里 s 在 x 方向，就把材料张量或样品坐标旋转到程序坐标系中。
```

---

## 3. 各向异性层的介电张量写法

### 3.1 未旋转主轴张量

单轴或双轴材料先写成本征主轴形式：

```python
import numpy as np

eps = np.diag([nx**2, ny**2, nz**2])
```

如果是各向同性层：

```python
eps = np.diag([n**2, n**2, n**2])
```

这也是把各向同性层纳入 4×4 框架的最稳方式。

### 3.2 旋转光轴

如果材料主轴相对实验坐标旋转，使用：

```text
ε_rot = R · ε · R^T
```

注意不是 `R^T ε R`，具体取决于你定义的是主动旋转还是坐标变换。对于 pyllama 风格，常用写法是：

```python
eps_rot = R @ eps @ R.T
```

经验检查：

- 各向同性张量旋转后应完全不变；
- 旋转 0° 后应回到原张量；
- 绕 z 轴旋转只会混合 x/y，不应改变 z 主轴分量；
- 如果旋转后出现不对称张量，通常是矩阵乘法顺序或数值误差问题。

---

## 4. 4×4 Berreman 方法的核心状态量

推荐使用切向场作为状态向量：

```text
ψ = [Ex, Hy, Ey, -Hx]^T
```

它的优点是边界条件清楚：在界面处切向 E、H 连续。

每个均匀层满足：

```text
dψ/dz = i k0 D ψ
```

或不同文献中可能写成 `-i k0 Q ψ`。符号差异来自时间因子约定：

```text
exp(-iωt) 与 exp(+iωt) 会导致传播相位符号不同。
```

所以不要只看矩阵元素，还要检查最终物理结果：

```text
无吸收单层：R + T ≈ 1
无结构均匀介质：R 接近 Fresnel 结果
法向各向同性 DBR：与 2×2 TMM 一致
```

---

## 5. pyllama 使用经验

### 5.1 最小可行结构

pyllama 中常用对象关系是：

```text
Model / StackModel
 └── Structure
      ├── entry HalfSpace
      ├── layers: Layer list
      └── exit HalfSpace
```

普通多层膜建议直接用 `StackModel`：

```python
model = ll.StackModel(
    eps_list=eps_list,
    thickness_nm_list=d_list,
    n_entry=1.0,
    n_exit=1.0,
    wl_nm=wl,
    theta_in_rad=np.deg2rad(theta),
    N_per=1
)
R, T = model.get_refl_trans(method="SM")
```

### 5.2 反射率矩阵的含义

pyllama 的线偏振结果通常是 2×2 矩阵：

```text
R = [[R_p_to_p, R_s_to_p],
     [R_p_to_s, R_s_to_s]]

T = [[T_p_to_p, T_s_to_p],
     [T_p_to_s, T_s_to_s]]
```

因此：

```python
R_p = R[0, 0] + R[1, 0]   # 入射 p，总反射到 p 和 s
T_p = T[0, 0] + T[1, 0]

R_s = R[0, 1] + R[1, 1]   # 入射 s，总反射到 p 和 s
T_s = T[0, 1] + T[1, 1]
```

如果材料无偏振转换，交叉项应接近 0：

```text
R_s_to_p ≈ 0
R_p_to_s ≈ 0
T_s_to_p ≈ 0
T_p_to_s ≈ 0
```

如果你只取 `R[0,0]` 或 `R[1,1]`，在有偏振转换时会漏掉能量。

### 5.3 优先使用 scattering matrix

多层膜层数较多、厚度较大、反射很强时，普通 transfer matrix 容易数值不稳定。经验上优先：

```python
method="SM"
```

只有在做公式对照或简单少层结构时，再比较：

```python
method="TM"
method="EM"
```

如果三者结果差异很大，优先相信 `SM`，同时检查层顺序、厚度单位和吸收符号。

---

## 6. 厚度设计经验

### 6.1 各向同性 DBR

中心波长 `λ0` 下，四分之一波厚度：

```text
d_H = λ0 / (4 n_H)
d_L = λ0 / (4 n_L)
```

如果波长单位是 nm，厚度也用 nm。不要把 μm 和 nm 混用。

### 6.2 各向异性 DBR

各向异性层不能只说一个折射率。要根据入射偏振和传播方向判断有效折射率。

保守做法：

```text
先用目标偏振对应的主折射率设计初始厚度；
再用 4×4 方法扫波长和角度；
最后通过峰位偏移反调厚度。
```

例如：

- s 光沿 y，则优先用 `ny` 设计 s 光中心波长；
- p 光会同时涉及 x/z 分量，不能简单只用 `nx` 或 `nz`；
- 若光轴旋转，直接通过 4×4 数值优化厚度更可靠。

### 6.3 半周期层数

如果设计 `6.5 pairs` 且第一层是高折射率 TiO2，第二层是 SiO2，常见理解是：

```text
TiO2 / SiO2 重复 6 次，再加一层 TiO2
```

即总层数 13 层。如果用户明确说“6.5 对”但没有说明终止层，需要在程序中写清楚终止层约定。

---

## 7. 角度扫描经验

角度扫描时，应固定入射介质中的角度：

```python
theta_in_rad = np.deg2rad(theta_deg)
Kx = n_entry * sin(theta_in_rad)
```

注意：

- 如果 `n_entry > n_exit`，大角度可能出现全反射；
- `theta_out = arcsin(n_entry/n_exit * sin(theta_in))` 可能变成复数；
- 程序中要允许 complex angle 或 complex Kz；
- 透射率前因子需要使用 `Kz_exit / Kz_entry` 或等价的能流修正。

绘制角度-波长赝色图时，推荐保存四张：

```text
R_s, T_s, R_p, T_p
```

如果有交叉偏振，额外保存：

```text
R_s_to_p, R_p_to_s, T_s_to_p, T_p_to_s
```

---

## 8. 能量守恒与 sanity check

每次写完程序，至少做以下检查。

### 8.1 无吸收各向同性单层

```text
R_s + T_s ≈ 1
R_p + T_p ≈ 1
```

允许误差通常应小于 `1e-6 ~ 1e-4`，具体取决于层数和角度。

### 8.2 各向同性极限

把各向异性层设置为：

```text
nx = ny = nz
```

则 4×4 程序应退化到普通 2×2 TMM 结果。

### 8.3 零厚度极限

若所有层厚度设为 0，则结果应该等价于 entry 到 exit 的单界面 Fresnel 反射。

### 8.4 周期数收敛

DBR 的周期数增加时：

```text
禁带反射率上升；
禁带边缘变陡；
谱线振荡增多。
```

如果周期数增加反而反射率乱跳，优先检查矩阵乘法顺序和层顺序。

### 8.5 光轴旋转对称性

如果每层都是各向同性，旋转角变化不应改变结果。

如果是单轴材料绕 z 轴旋转：

```text
法向入射时，s/p 结果会随光轴相对方向变化；
若旋转 90°，x/y 主折射率效果应互换。
```

---

## 9. 常见错误和快速定位

### 错误 1：把 `nx, ny, nz` 当成 `εxx, εyy, εzz`

正确是：

```python
eps = np.diag([nx**2, ny**2, nz**2])
```

不是：

```python
eps = np.diag([nx, ny, nz])
```

### 错误 2：厚度单位混乱

pyllama 中常用：

```text
wl_nm: nm
thickness_nm_list: nm
```

如果你输入 `0.1`，那是 `0.1 nm`，不是 `0.1 μm`。

### 错误 3：把矩阵元素当作总反射

有偏振转换时，总反射要按入射列求和：

```python
R_s_total = R[0,1] + R[1,1]
R_p_total = R[0,0] + R[1,0]
```

### 错误 4：直接用 2×2 算旋转各向异性层

只要光轴旋转后出现非对角介电张量，2×2 通常不再可靠。

### 错误 5：层顺序反了

光从 entry 入射，layers 列表顺序应为：

```text
第一层接触入射介质，最后一层接触出射介质。
```

DBR 里“第一层 TiO2”就是 `eps_list[0] = eps_TiO2`。

### 错误 6：把 s 光方向和程序默认方向混淆

pyllama 默认入射面通常按 x-z 处理，因此 s 光沿 y。若你的物理定义中 s 沿 x，需要转换坐标，而不是直接把 `nx` 当成 s 光折射率。

---

## 10. 推荐代码模板：各向同性 / 各向异性统一写法

```python
import numpy as np
import matplotlib.pyplot as plt
import pyllama as ll


def eps_iso(n):
    return np.diag([n**2, n**2, n**2])


def eps_aniso(nx, ny, nz):
    return np.diag([nx**2, ny**2, nz**2])


def rotz(angle_deg):
    a = np.deg2rad(angle_deg)
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0],
                     [s,  c, 0],
                     [0,  0, 1]])


def rotate_eps(eps, angle_deg):
    R = rotz(angle_deg)
    return R @ eps @ R.T


def calc_stack_rt(wl_nm, theta_deg, eps_list, d_list_nm, n_entry=1.0, n_exit=1.0):
    model = ll.StackModel(
        eps_list=eps_list,
        thickness_nm_list=d_list_nm,
        n_entry=n_entry,
        n_exit=n_exit,
        wl_nm=wl_nm,
        theta_in_rad=np.deg2rad(theta_deg),
        N_per=1
    )
    R, T = model.get_refl_trans(method="SM")

    Rp = np.real(R[0, 0] + R[1, 0])
    Tp = np.real(T[0, 0] + T[1, 0])
    Rs = np.real(R[0, 1] + R[1, 1])
    Ts = np.real(T[0, 1] + T[1, 1])

    return Rs, Ts, Rp, Tp, R, T


# example: 6.5-pair isotropic DBR
lambda0 = 920.0
nH = 2.35
nL = 1.45
pairs = 6

H = eps_iso(nH)
L = eps_iso(nL)
dH = lambda0 / (4 * nH)
dL = lambda0 / (4 * nL)

eps_list = []
d_list = []
for _ in range(pairs):
    eps_list += [H, L]
    d_list += [dH, dL]
# extra half pair: one more high-index layer
eps_list.append(H)
d_list.append(dH)

wls = np.linspace(700, 1200, 501)
Rs_list, Rp_list = [], []
for wl in wls:
    Rs, Ts, Rp, Tp, _, _ = calc_stack_rt(wl, 0, eps_list, d_list)
    Rs_list.append(Rs)
    Rp_list.append(Rp)

plt.figure(figsize=(6, 4))
plt.plot(wls, Rs_list, label="s")
plt.plot(wls, Rp_list, "--", label="p")
plt.xlabel("Wavelength (nm)")
plt.ylabel("Reflectance")
plt.legend()
plt.tight_layout()
plt.show()
```

---

## 11. 我在之后回答这类问题时应遵循的工作流

1. 先判断结构：各向同性、单轴、双轴、旋转光轴、连续变化光轴。
2. 明确坐标系：z 为膜法线，入射面是 x-z，s 光沿 y。
3. 所有材料统一写成 3×3 介电张量。
4. 如果有旋转，先旋转张量，不直接旋转折射率标量。
5. 层厚单位全部用 nm，波长也用 nm。
6. 优先用 scattering matrix，尤其是 DBR、高反、多周期结构。
7. 输出不只给 `R[0,0]`，而是给入射 s/p 的总反射和总透射。
8. 对无吸收结构检查 `R + T ≈ 1`。
9. 对各向同性极限，与 2×2 TMM 或 Fresnel 公式对照。
10. 如果画赝色图，横轴波长、纵轴角度、颜色为 R/T，并标注 s/p 与是否包含交叉偏振。

---

## 12. 一句话经验

各向同性膜堆可以用 2×2 快速算，但只要出现光轴旋转、nx/ny/nz 不相等、液晶扭曲或偏振转换，就应该切换到 4×4 Berreman / scattering matrix；并且最终判断正确性的核心不是矩阵形式看起来多复杂，而是坐标系、偏振定义、能流归一化和能量守恒是否全部自洽。
