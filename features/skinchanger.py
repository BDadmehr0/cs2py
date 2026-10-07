import struct
import time
from functions import memfuncs

# ==================== Skin Map ====================
SKIN_MAP = {
    7:   44,     # AK-47 → Case Hardened
    9:   344,    # AWP → Dragon Lore
    16:  309,    # M4A4 → Howl
    60:  445,    # M4A1-S → Hyper Beast
    4:   38,     # Glock → Fade
    61:  653,    # USP-S → Kill Confirmed
    1:   37,     # Deagle → Blaze
    # بقیه رو خودت اضافه کن
}

def get_weapon_paint(item_def: int) -> int:
    return SKIN_MAP.get(item_def, 0)


def GetEntityFromHandle(processHandle, ListEntries, handle):
    if not handle or handle == 0xFFFFFFFF:
        return 0
    try:
        list_entry = ListEntries[(handle & 0x7FFF) >> 9]
        if not list_entry:
            return 0
        return memfuncs.ProcMemHandler.ReadPointer(
            processHandle, list_entry + 0x70 * (handle & 0x1FF)
        )
    except:
        return 0


# برای جلوگیری از force update مکرر
_last_force_time = 0
_last_active_weapon = 0

def SkinChanger_Update(processHandle, clientBaseAddress, Offsets, Options):
    global _last_force_time, _last_active_weapon

    if not Options.get("EnableSkinChanger", False):
        return

    try:
        # ---------- Entity List ----------
        EntityList = memfuncs.ProcMemHandler.ReadPointer(
            processHandle, clientBaseAddress + Offsets.offset.dwEntityList
        )
        if not EntityList:
            return

        ListEntries = struct.unpack(
            "64Q",
            memfuncs.ProcMemHandler.ReadBytes(processHandle, EntityList + 0x10, 64 * 8)
        )

        # ---------- Local Pawn ----------
        local_pawn = memfuncs.ProcMemHandler.ReadPointer(
            processHandle, clientBaseAddress + Offsets.offset.dwLocalPlayerPawn
        )
        if not local_pawn:
            return

        health = memfuncs.ProcMemHandler.ReadInt(processHandle, local_pawn + Offsets.offset.m_iHealth)
        if health <= 0:
            return

        # ---------- Weapon Services ----------
        weapon_services = memfuncs.ProcMemHandler.ReadPointer(
            processHandle, local_pawn + Offsets.offset.m_pWeaponServices
        )
        if not weapon_services:
            return

        need_force_update = False

        # ---------- همه سلاح‌های اینونتوری (مهم) ----------
        for i in range(8):  # معمولاً حداکثر ۸ اسلات
            try:
                weapon_handle = memfuncs.ProcMemHandler.ReadUInt(
                    processHandle,
                    weapon_services + Offsets.offset.m_hMyWeapons + (i * 4)
                )
                if not weapon_handle:
                    continue

                weapon = GetEntityFromHandle(processHandle, ListEntries, weapon_handle)
                if not weapon:
                    continue

                item_def = memfuncs.ProcMemHandler.ReadShort(
                    processHandle,
                    weapon + Offsets.offset.m_AttributeManager +
                    Offsets.offset.m_Item + Offsets.offset.m_iItemDefinitionIndex
                )

                paint = get_weapon_paint(item_def)
                if paint == 0:
                    continue

                current_paint = memfuncs.ProcMemHandler.ReadInt(
                    processHandle, weapon + Offsets.offset.m_nFallbackPaintKit
                )

                if current_paint != paint:
                    # 1. ItemIDHigh = -1
                    memfuncs.ProcMemHandler.WriteUInt(
                        processHandle,
                        weapon + Offsets.offset.m_AttributeManager +
                        Offsets.offset.m_Item + Offsets.offset.m_iItemIDHigh,
                        0xFFFFFFFF
                    )

                    # 2. PaintKit
                    memfuncs.ProcMemHandler.WriteInt(
                        processHandle, weapon + Offsets.offset.m_nFallbackPaintKit, paint
                    )

                    # 3. Wear
                    memfuncs.ProcMemHandler.WriteFloat(
                        processHandle, weapon + Offsets.offset.m_flFallbackWear, 0.001
                    )

                    # 4. Seed
                    memfuncs.ProcMemHandler.WriteInt(
                        processHandle, weapon + Offsets.offset.m_nFallbackSeed, 0
                    )

                    # 5. AttributesInitialized = False (خیلی مهم برای اعمال اسکین)
                    # آفست تقریبی - اگر کار نکرد باید از dumper بگیری
                    try:
                        memfuncs.ProcMemHandler.WriteBool(
                            processHandle, weapon + Offsets.offset.m_AttributeManager - 8, False
                        )
                    except:
                        pass

                    need_force_update = True

            except:
                continue

        # ---------- Force Update فقط وقتی لازم باشه + با cooldown ----------
        current_time = time.time()
        if need_force_update and (current_time - _last_force_time > 1.5):  # حداقل ۱.۵ ثانیه فاصله
            try:
                engine = memfuncs.GetModuleBase("engine2.dll", processHandle)
                if engine:
                    net_client = memfuncs.ProcMemHandler.ReadPointer(
                        processHandle, engine + Offsets.offset.dwNetworkGameClient
                    )
                    if net_client:
                        memfuncs.ProcMemHandler.WriteInt(
                            processHandle,
                            net_client + Offsets.offset.dwNetworkGameClient_deltaTick,
                            -1
                        )
                        _last_force_time = current_time
                        print("[SkinChanger] Force update done")  # برای دیباگ
            except:
                pass

    except Exception:
        pass
