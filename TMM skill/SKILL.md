# Skill: 各向同性 / 各向异性传输矩阵建模

## 目标

帮助用户建立、检查和修改用于多层膜、DBR、各向异性薄膜、液晶层、旋转光轴结构的传输矩阵程序。优先保证物理定义正确、数值稳定、输出结果可解释。

## 默认物理约定

除非用户明确要求改变，否则采用以下约定：

- 膜层法线为 z 方向。
- 光从 entry 半空间向 exit 半空间沿 +z 方向入射。
- 入射面为 x-z 平面。
- s 光电场沿 y 方向。
- p 光电场在 x-z 平面内。
- 切向波矢为 `Kx = n_entry * sin(theta_in)`，`Ky = 0`。
- 所有波长和厚度默认使用 nm。

如果用户说“x 方向是 s 光方向”，不要直接把默认公式中的 s/p 对调。应说明默认程序中 s 沿 y；若物理 s 沿 x，需要把材料张量或样品坐标转换到程序坐标中，或者重新定义入射面为 y-z。

## 方法选择规则

### 可使用 2×2 TMM 的情况

当所有层均为各向同性，且无偏振转换时，可使用 2×2 TMM 分别计算 s/p。

判断条件：

```text
ε = diag(n², n², n²)
```

### 应使用 4×4 Berreman 的情况

只要出现以下任一情况，应使用 4×4：

- `nx ≠ ny` 或 `ny ≠ nz`。
- 材料光轴相对实验坐标旋转。
- 液晶 director 沿 z 变化。
- 扭曲向列、胆甾相、分片旋转结构。
- 需要计算交叉偏振项，如 `R_s_to_p`、`T_p_to_s`。
- 用户关心各向异性 DBR、偏振选择性反射、s/p 耦合。

## 建模步骤

1. 询问或从上下文确认材料参数：`nx, ny, nz` 或 `n`。
2. 把所有材料统一写为 3×3 介电张量：

```python
eps_iso = np.diag([n**2, n**2, n**2])
eps_aniso = np.diag([nx**2, ny**2, nz**2])
```

3. 若存在旋转，使用：

```python
eps_rot = R @ eps @ R.T
```

4. 构造层列表时，保证第一层就是接收入射光的第一层。
5. 厚度单位必须和波长单位一致，默认均为 nm。
6. 对多周期、高反射、DBR，优先使用 scattering matrix，即 pyllama 中的 `method="SM"`。
7. 输出 s/p 总反射和总透射，而不是只输出矩阵对角元。

## pyllama 输出解释

pyllama 的线偏振反射 / 透射矩阵按如下方式理解：

```text
R = [[R_p_to_p, R_s_to_p],
     [R_p_to_s, R_s_to_s]]

T = [[T_p_to_p, T_s_to_p],
     [T_p_to_s, T_s_to_s]]
```

因此：

```python
R_p_total = R[0, 0] + R[1, 0]
T_p_total = T[0, 0] + T[1, 0]
R_s_total = R[0, 1] + R[1, 1]
T_s_total = T[0, 1] + T[1, 1]
```

若用户只要普通 s/p 曲线，默认给出这些总量。

## 必须做的 sanity checks

在给出最终程序或结论前，尽量加入这些检查：

1. 无吸收结构：`R_s + T_s ≈ 1`，`R_p + T_p ≈ 1`。
2. 各向同性极限：`nx = ny = nz` 时，4×4 结果应与 2×2 TMM 一致。
3. 零厚度极限：所有层厚度为 0 时，应退化为 entry/exit 单界面 Fresnel 结果。
4. 各向同性层旋转后结果不变。
5. 增加 DBR 周期数时，禁带反射率应升高，边缘应变陡。

## 常见错误提醒

- 不要把折射率直接放入介电张量；应放 `n²`。
- 不要混用 μm 和 nm。
- 不要在有偏振转换时只取 `R[0,0]` 或 `R[1,1]` 当总反射。
- 不要用 2×2 TMM 处理旋转各向异性层。
- 不要忽略透射能流修正因子，尤其是斜入射和 entry/exit 折射率不同的情况。
- 不要在未定义坐标系时讨论“x 方向是 s 光”。

## 推荐回答结构

当用户请求程序时，按以下结构回答：

1. 简短说明采用的坐标系和物理假设。
2. 给出完整可运行 Python 程序。
3. 明确说明 `R_s, T_s, R_p, T_p` 的定义。
4. 若有交叉偏振，说明总量如何求和。
5. 加入能量守恒检查输出。
6. 若画图，优先输出：
   - 波长曲线：`R_s, R_p` 或 `T_s, T_p`。
   - 赝色图：横轴波长，纵轴角度，颜色为 R/T。
7. 对复杂各向异性结构，提醒用户检查收敛性和层数切片。

## 推荐代码片段

```python
import numpy as np


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


def rotate_eps_z(eps, angle_deg):
    R = rotz(angle_deg)
    return R @ eps @ R.T


def total_sp_from_pyllama(R, T):
    Rp = np.real(R[0, 0] + R[1, 0])
    Tp = np.real(T[0, 0] + T[1, 0])
    Rs = np.real(R[0, 1] + R[1, 1])
    Ts = np.real(T[0, 1] + T[1, 1])
    return Rs, Ts, Rp, Tp
```

## 对用户的偏好

用户经常需要完整程序而不是只要理论说明。回答时应尽量给出可直接运行的代码，并对关键物理假设做简明解释。对于 pyllama、各向异性 TMM、DBR、角度-波长赝色图，优先给出完整脚本。
