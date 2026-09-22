# 工程生成配置

仅在新建或参数化修改平面液晶柱透镜工程时阅读本文件。所有几何量用 µm，电压用 V，时间用 s，角度用 deg。

## 最小可运行示例

```json
{
  "name": "LC_Lens_P200_5seg",
  "pitch": 200,
  "Ly": 10,
  "gap": 25,
  "glass": 5,
  "ito": 0.05,
  "pi": 0.1,
  "ne": 1.77,
  "no": 1.47,
  "pretilt": 2,
  "azimuth": 90,
  "lc_layers": 16,
  "mesh_len": 1.5,
  "mesh_max": 3,
  "material": "LC-LENS-DN030",
  "time_final_s": 1.0,
  "time_step_s": 0.001,
  "data_out_step": 1000,
  "electrodes": [
    {"name": "E1_EDGE", "centers": [-100, 100], "width": 10.57, "type": "SWEEP", "start": 0, "stop": 11, "step": 1},
    {"name": "E2_MID", "centers": [-60, 60], "width": 10.57, "type": "DC", "v": 2.0},
    {"name": "E3_CEN", "centers": [-20, 20], "width": 10.57, "type": "DC", "v": 1.0}
  ],
  "signal": [[0, 0], [0.01, 0], [0.011, 11], [1.0, 11], [1.001, 0], [4.0, 0]],
  "signal_electrode": "E1_EDGE"
}
```

运行：

```powershell
python scripts/new_lc_lens_project.py config.json --template D:\path\to\validated-template
```

若输出目录已含生成文件，脚本默认退出；确认目标后才加 `--force`。可用 `--output` 覆盖输出目录。模板选择优先级为 `--template`、JSON 的 `template_dir`、环境变量 `TECHWIZ_TEMPLATE_DIR`；未指定模板时脚本退出，不猜测本机目录。

## 字段与约束

- `name`：安全文件名，只允许字母、数字、点、下划线和连字符。
- `pitch`、`Ly`、`gap`、`glass`、`ito`、`pi`：周期、Y 尺寸、盒厚及层厚。
- `ne`、`no`：脚本采用正单轴模型，要求 `ne > no > 0`。
- `pretilt`、`azimuth`：上下基板使用同一组配向角；TN 不应套用这个生成器。
- `lc_layers`、`mesh_len`、`mesh_max`：LC 分层和网格参数，且 `mesh_len <= mesh_max`。
- `material`：必须已存在于模板的材料库中；生成器不会猜测材料参数。
- `electrodes`：顶部电极组。同组多个中心写进同一个 `ELECTRODE`，因而保持同电位。中心允许位于 `±pitch/2`，生成器会裁为周期边界两半条。
- 每个工程必须恰有一个非 DC 电极，作为 `Main`；支持 `SWEEP` 或 `SIGNAL`。`SWEEP` 要有 `start`、`stop`、`step`，`DC` 要有 `v`。
- `aperture`：可选。未给出时，如果存在周期边界电极，默认 `pitch - boundary_electrode_width`；否则默认整个周期。
- `wavelength_nm`：可选，默认 550 nm，仅用于把 OPD 换算为波数。
- `polarizer_absorb_phi`：可选，默认 0°；注意这是吸收轴，0° 对应 Y 向透过轴。
- `signal`、`signal_electrode`：可选响应工程。时间必须严格递增；信号电极必须与主扫描电极相同。生成后的参数文件保留波形，响应脚本据此推断开关时刻。
- `resp_data_out_step`：响应工程输出步长，默认 10。
- `template_project`：模板目录含多个非响应 `.prj` 时，用它指定文件名。
- `material_db`、`light_source_db`：可选模板资产名，默认 `Material_LC_Lens.db` 和 `LightSource.ldb`。即使使用 `--force`，生成器也不会覆盖输出目录中已有的材料库或光源库。

## 模板要求

模板必须是 TechWiz 15 已成功打开并至少完成过 Mesh Generation 的工程。生成器只做有限字段替换，并验证以下关键块存在：`MaterialDB`、`SignalDB`、`StrFile`、`EltFile`、`StkFile`、网格/时间字段和 `RUBBING Zones`。不要用从零猜测格式的 `.str` 充当模板。

生成后仍需在 GUI 中核对电极表、周期边界、配向区和材料，再运行求解器。生成成功不等于仿真成功。
