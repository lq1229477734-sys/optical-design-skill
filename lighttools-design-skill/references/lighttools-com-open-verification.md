# LightTools COM Open Verification

Use this reference when a patched `.lts` model opens through LightTools COM but
the exported receiver TXT files are identical to an older baseline.

## Failure Mode

LightTools COM can report `Open` status `0` while the active model is not the
patched file you intended. This can happen with extra dots in filenames. For
example, opening:

```text
distance.bps.6.ec_t65_work_verified.lts
```

may leave the active model equivalent to:

```text
distance.bps.6.lts
```

even though the automation wrote the requested path into logs or TXT headers.
Treat logs and self-written TXT headers as requested-path records, not proof of
the active LightTools model.

## Safe Filename Rule

For patched models used by COM automation, avoid extra dots before `.lts`.
Prefer underscores:

```text
distance_bps6_ec_t65_work_verified.lts
```

Keep the original model unchanged, and copy patched versions to safe filenames
before scanning.

## Required Open Procedure

Before opening a scan model:

```powershell
LT-Cmd '\VConsole' | Out-Null
LT-SetOption 'ShowDialogs' 0 | Out-Null
LT-SetOption 'ShowFileDialogBox' 0 | Out-Null
LT-SetOption 'ConfirmDeleteModel' 0 | Out-Null
$newStatus = LT-Cmd 'New'
$openStatus = LT-Cmd ('Open ' + (LT-Str $resolvedModel))
```

Record `$newStatus`, `$openStatus`, the resolved model path, and the receiver
mesh key in the scan log.

## Proof Before Full Sweep

Before launching a full parameter sweep, prove the active model:

1. Save a proof copy immediately after `Open`, then inspect the proof file for
   the patched property value, such as `ec_t` `setTransmittance: 0.65;`.
2. Run one scan parameter point and compare its full 61 x 61 TXT mesh against
   the old baseline with hashes and numerical differences.
3. Continue only if the one-point result changes as expected.

Example from a `distance.bps.6` `ec_t` scan:

```text
Old 1% baseline center luminance: 190.182933
Correct 65% center luminance:    240.468484
```

The correct result was obtained only after copying the patched model to a safe
underscore filename and opening with `New` before `Open`.

## If Results Are Still Identical

If the proof copy has the patched value but TXT meshes remain identical:

- Verify that the scanned surface or texture actually references the patched
  optical property, for example `setPropertiesName: "ec_t";`.
- Test an extreme one-point patch such as transmittance `0` or `1`.
- Dump the receiver and angular-luminance mesh keys with `DbKeyDump` and ensure
  the script exports the intended `BLUReceiver` `Angular_Luminance_Mesh`.
