# TC1782 UCB Locker — Open-Source CLI/GUI Helper  
Lock the **U-Code Bytes (UCB)** of Continental / Infineon **TriCore TC1782** engine-control units.

> **⚠️  PERMANENT RISK**  
> Writing bad data into the UCB sector can *irreversibly* brick an ECU.  
> Always keep an **unaltered backup** and verify every byte the tool shows you before flashing.

---

## What the Tool Does

| UCB Page | Action | Default | Option |
|---------:|--------|---------|--------|
| **0** | – Write a 5-byte OCDS password<br>– Set **OCDSLCK** bit (locks OCDS)<br>– Set **FPROTEN0/1** bits (locks flash sectors 0 & 1) | ✓ | – |
| **3** | – Block CAN/boot-loader erase & write by clearing bit 0 | ✗ | `--block-bsl` / checkbox |
| **4 – 7** | – (If requested) mirror the same edits into the four redundant UCB copies | ✗ | `--patch-mirrors` / checkbox |

After patching, the tool **re-computes the additive checksums** on every modified page and saves  
`<dump>_locked.bin` next to the original dump.

---

## Supported Dumps

* Raw **32 × 0x20-byte EEPROM** images (Infineon internal EEPROM area).  
* No ECU is read or written directly – you work on a file exported by a modern flash tool
  (VF2, CMDFlash, …).

---

## Quick Start ( CLI )

```bash
python3 ucb_lock_cli.py         --dump Bench_SIM2K-25x_IntEeprom.bin         --pwd D4E7A19C3F         --block-bsl        \         # optional
        --patch-mirrors              # optional
```

The script will:

1. Validate size (must be multiple of `0x20` bytes).  
2. Show a diff-style report of **before → after** values.  
3. Write `Bench_SIM2K-25x_IntEeprom_locked.bin`.

Nothing is flashed until **you** program the resulting file back with your preferred tool.

---

## Quick Start ( GUI )

```bash
python3 ucb_lock_gui.py      # minimal GUI  
python3 ucb_lock_gui_debug.py  # GUI + pop-up diff for every run
```

1. Pick the EEPROM dump.  
2. Enter a 10-digit hex password (or press `Generate` in the GUI fork).  
3. Tick options as needed.  
4. Press **Lock UCB** and review the diff report.

---

## Generating a Secure Password

The CLI can auto-generate one:

```bash
python3 - <<'PY'
from secrets import token_hex
print(token_hex(5).upper())   # 10 hex chars
PY
```

Or ask the tool itself (`--auto-pwd`).

---

## Safety Checklist

1. **Backup twice.** Keep the untouched dump in version control.
2. **Verify the diff.** The tool highlights every bit it changes; read it.
3. **Program using “verify after write”.** If your flasher offers it, enable it.
4. **Have BSL/PIN-boot access ready.** In case something still goes wrong.

---

## License

[MIT](LICENSE).  Use at your own risk – **no warranty** for damaged ECUs, lost time,  
or any other consequences.

---

## Credits

* Reverse-engineering community @ **mhh-auto**, **Trionic & OpenECU**.  
* Based on public Infineon documents *AP32219*/*AP32354* ( TriCore® Boot ROM ).

Happy hacking & stay safe!
