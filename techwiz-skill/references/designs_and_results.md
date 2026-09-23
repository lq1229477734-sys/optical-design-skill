# 已完成的工程、设计推导与结果（截至 2026-09-21）

这些数据是特定 TechWiz v15 工程的回归基准，不是材料或结构的普适性能。只有在几何、材料、配向、偏振、波长、孔径、网格、模拟时长和指标定义一致时才可直接比较；引用结果时保留工程名和条件。

## 1. TN_Cylindrical_Lens / TN_Cylindrical_Lens_Run — TN 液晶柱透镜（第一个模型）
- pitch 200 µm，Y 10 µm；孔径 160 µm；顶部左右 ITO 各 20 µm（x=±80…±100）；底部整面 ITO。
- LC-TN（K 11.7/5.5/14.0 pN，ε 8.6/3.3，γ1 85 mPa·s，ne/no 1.5977/1.4937），盒厚 20 µm；下 2°/0°、上 2°/90°（90° TN）。
- 流程：`build_tn_cyl_lens_package.py` 生成 GDS/TEC/SIF/zones.csv → Layout 原生 Generate `.str` → `TN_Cylindrical_Lens_READY.prj`。
- 稳态：0–8 V 扫描，30 ms；Mesh 20358 节点。
- 响应（0→8→0 V，`TN_Response_8V`，双偏振片）：t_on = 105.5 ms，t_off = 447.1 ms，合计 552.6 ms（光学 10–90%）。
- 教训：离线手写 `.str` 使 Mesh 卡死 → 已改名 `*_unverified.str`，不要用。TN 做透镜偏振行为复杂，后续改用均匀配向。

## 2. LC_Lenticular_Lens — 纯液晶柱透镜"最优方案 1"（Δn = 0.10）
- 取自"液晶透镜仿真(总结)"最优行：pitch 141.88 µm，顶部单条 ITO 7.5 µm 位于周期边界，底部整面 COM，盒厚 25 µm，11 V。
- LC-LENS-DN010，均匀配向 2°/90°（沿 Y），单偏振片 Phi=0（透过 Y）。
- 结果（TimeFinal 0.3 s）：11 V：dOPD 2113 nm（3.84 λ），f = 1.055 mm，RMSE_norm 0.0355；9 V 附近 f 最短 1.047 mm。
- 响应（0→11 V@10 ms，11→0 V@1000 ms）：t_on = 59.5 ms，t_off = 758.9 ms；on-state Δn 深度 0.0846。
- 生成脚本：`build_planar_lc_lens_model.py`（注意其中 stk 的 Phi=90 是旧错误，工程内已改为 0）。

## 3. LC_Lens_P200_DN030 — 200 µm 单电极（Δn = 0.30）基准
- pitch 200，边界电极 10.57 µm，盒厚 25 µm，LC-LENS-DN030（1.77/1.47），0–11 V。
- 11 V：dOPD 6206 nm（11.28 λ），f = 0.687 mm，RMSE_norm 0.0695（抛物线偏差明显）。

## 4. LC_Lens_P200_5seg — 200 µm 五分段电极（Δn = 0.30）当前主线
- 5 个 40 µm 单元；电极 10.57 µm，中心 x=±100（半条）、±60、±20；BOT_COM 0 V。
- 分组：E1_EDGE（±100）扫 0–11 V；E2_MID（±60）DC 2.0 V；E3_CEN（±20）DC 1.0 V（略低于阈值 ~1.5 V）。
- 电压设计：理想抛物线要求相对开启比例 s(x)=(x/100)²；用 1D Frank–Oseen 求 Δn_eff/Δn–V：1.5 V→0.93、2.0→0.67、2.5→0.47、3→0.34、5→0.17、11→0.07。x=±60 需 ≈0.66 → V2≈2.0 V（约 V1 的 18%）。阈值附近曲线极陡，故另做扫描。
- 工程：主工程（E1 扫描）、V2scan（E1=11，E2 1.0–4.0/0.5）、V3scan（E1=8，E2=2，E3 1.0–2.0/0.25）、Response（E1 阶跃 11 V，4 s）。
- 结果（`LENS_ANALYSIS/summary.csv`，最新）：

| V1 (V) | dOPD (nm) | f (mm) | RMSE_norm |
|---|---|---|---|
| 4 | 5171 | 0.972 | 0.0749 |
| 6 | 5830 | 0.774 | 0.0430 |
| 8 | 6033 | 0.724 | **0.0392** |
| 11 | 6181 | 0.694 | 0.0423 |

- V2 扫描（E1=11 V）：RMSE_norm 1.0 V 0.107 → 1.5 V 0.085 → **2.0 V 0.056** → 2.5 V 0.074 → 3.0 V 0.128，确认 V2 = 2.0 V 最优。
- 对比单电极 DN030（11 V RMSE 0.0695）：五分段把抛物线误差降约 40%，焦距基本不变（~0.69 mm）。
- `LENS_ANALYSIS-02` / `len-1` 为较早一版运行（配置未单独记录），11 V RMSE 0.046。
- 待办：V3scan、Response 的后处理结果尚未汇总。

生成相同五分段参数的 JSON 示例及字段约束见 [configuration.md](configuration.md)。
