#!/usr/bin/env python3
"""
ucb_lock_wizard.py  —  TC179x UCB Locker (step-by-step wizard)

What it does
------------
• Adds a 5-byte OCDS password and sets OCDSLCK + FPROTEN (UCB page-0)
• Can block CAN/BSL erase-write (page-3, bit-0)                [optional]
• Can copy that change to the four mirror pages 0x80-0xDF       [optional]
• Re-computes page checksums
• Saves  <dump>_locked.bin
• Prints a detailed before/after report to your terminal
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

# ───────────────────────── constants ─────────────────────────
PAGE        = 0x20
PAGE0_OFF   = 0x00
PAGE3_OFF   = 0x60
MIRROR_OFFS = (0x80, 0xA0, 0xC0, 0xE0)


# ──────────────────────── helpers ────────────────────────────
def checksum(page: memoryview) -> int:
    """8-bit additive checksum (two’s complement of bytes 0-0x1D)."""
    return (-sum(page[:0x1E])) & 0xFF


def patch_page0(page: memoryview, pwd_hex: str) -> str:
    old_pwd  = page[0x10:0x15].tobytes().hex().upper()
    old_ocds = page[0x1A] & 1
    old_fp0  = page[0x1C] & 1
    old_fp1  = page[0x1D] & 1
    old_cs   = page[0x1E]

    # apply edits
    page[0x10:0x15] = bytes.fromhex(pwd_hex)
    page[0x1A]     |= 1         # OCDSLCK
    page[0x1C]     |= 1         # FPROTEN0
    page[0x1D]     |= 1         # FPROTEN1
    page[0x1E]      = checksum(page)

    new_pwd  = page[0x10:0x15].tobytes().hex().upper()
    new_ocds = page[0x1A] & 1
    new_fp0  = page[0x1C] & 1
    new_fp1  = page[0x1D] & 1
    new_cs   = page[0x1E]

    return textwrap.dedent(f"""
        -- Page 0 (0x{PAGE0_OFF:04X}) --
          password       : {old_pwd} → {new_pwd}
          OCDSLCK bit    : {old_ocds} → {new_ocds}
          FPROTEN0 bit   : {old_fp0} → {new_fp0}
          FPROTEN1 bit   : {old_fp1} → {new_fp1}
          checksum       : {old_cs:02X} → {new_cs:02X}
    """).strip()


def patch_page3(page: memoryview, block: bool, offset: int) -> str:
    old_flag = page[0x08] & 1
    old_cs   = page[0x1E]

    if block:
        page[0x08] &= 0xFE       # clear bit-0
    page[0x1E] = checksum(page)

    new_flag = page[0x08] & 1
    new_cs   = page[0x1E]

    return textwrap.dedent(f"""
        -- Page @0x{offset:04X} --
          BSL write flag : {old_flag} → {new_flag}
          checksum       : {old_cs:02X} → {new_cs:02X}
    """).strip()


def ask_path(prompt: str) -> Path:
    while True:
        p = Path(input(prompt).strip().strip('"').strip("'"))
        if not p.is_file():
            print("  ✘ file not found — try again\n")
            continue
        return p


def ask_password() -> str:
    while True:
        pwd = input("Enter 10-digit OCDS password (hex, no spaces): ").strip()
        if len(pwd) != 10 or any(c not in "0123456789abcdefABCDEF" for c in pwd):
            print("  ✘ password must be exactly 10 hex characters\n")
            continue
        return pwd.upper()


def ask_yes_no(q: str, default: bool = False) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        ans = input(f"{q} {suffix}: ").strip().lower()
        if not ans:
            return default
        if ans in {"y", "yes"}:
            return True
        if ans in {"n", "no"}:
            return False
        print("  ✘ please type y or n\n")


# ──────────────────────── main wizard ────────────────────────
def main() -> None:
    print("\n====  TC179x UCB Locker (interactive)  ====\n")

    bin_path  = ask_path("Path to EEPROM dump (.bin): ")
    password  = ask_password()
    block_wrt = ask_yes_no("Block CAN/BSL erase-write?", default=True)
    mirror    = ask_yes_no("Patch the 4 mirror pages as well?", default=False)

    data = bytearray(bin_path.read_bytes())
    if len(data) % PAGE:
        sys.exit("ERROR: file size is not a multiple of 0x20 bytes")

    mv = memoryview(data)
    reports: list[str] = [patch_page0(mv[PAGE0_OFF:PAGE0_OFF+PAGE], password)]

    pages = [PAGE3_OFF] + list(MIRROR_OFFS) if mirror else [PAGE3_OFF]
    for off in pages:
        reports.append(patch_page3(mv[off:off+PAGE], block_wrt, off))

    out_path = bin_path.with_stem(bin_path.stem + "_locked")
    out_path.write_bytes(data)

    print("\n".join(reports))
    print(f"\n✔  Saved as: {out_path}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted — no changes written.")
