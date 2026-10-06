import struct
from functions import memfuncs

def SkinChanger_Update(processHandle, clientBaseAddress, Offsets, Options):
    if not Options.get("EnableSkinChanger", False):
        return

    try:
        # ۱. خواندن EntityList و آماده‌سازی ListEntries (مثل ESP)
        EntityList = memfuncs.ProcMemHandler.ReadPointer(
            processHandle, clientBaseAddress + Offsets.offset.dwEntityList
        )
        if not EntityList:
            return

        # این خط خیلی مهمه - دقیقاً مثل ESP
        ListEntries = struct.unpack("64Q", memfuncs.ProcMemHandler.ReadBytes(
            processHandle, EntityList + 0x10, 64 * 8
        ))

        # ۲. گرفتن Local Player Pawn
        local_pawn = memfuncs.ProcMemHandler.ReadPointer(
            processHandle, clientBaseAddress + Offsets.offset.dwLocalPlayerPawn
        )
        if not local_pawn:
            return

        # ۳. خواندن WeaponServices
        weapon_services = memfuncs.ProcMemHandler.ReadPointer(
            processHandle, local_pawn + Offsets.offset.m_pWeaponServices
        )
        if not weapon_services:
            return

        # ۴. خواندن handle سلاح فعال
        active_weapon_handle = memfuncs.ProcMemHandler.ReadUInt(
            processHandle, weapon_services + Offsets.offset.m_hActiveWeapon
        )
        if not active_weapon_handle:
            return

        # ۵. تبدیل handle به pointer واقعی سلاح (مهم‌ترین بخش)
        active_weapon = GetEntityFromHandle(processHandle, ListEntries, active_weapon_handle)
        if not active_weapon:
            return

        # حالا active_weapon آدرس واقعی entity سلاح هست
        # از اینجا به بعد می‌تونی paintkit و ... رو روش بنویسی

        item_def = memfuncs.ProcMemHandler.ReadShort(
            processHandle,
            active_weapon + Offsets.offset.m_AttributeManager +
            Offsets.offset.m_Item + Offsets.offset.m_iItemDefinitionIndex
        )

        paint = get_weapon_paint(item_def)   # تابع خودت
        if paint == 0:
            return

        # اعمال اسکین
        current_paint = memfuncs.ProcMemHandler.ReadInt(
            processHandle, active_weapon + Offsets.offset.m_nFallbackPaintKit
        )

        if current_paint != paint:
            # ItemIDHigh رو -1 کن
            memfuncs.ProcMemHandler.WriteUInt(
                processHandle,
                active_weapon + Offsets.offset.m_AttributeManager +
                Offsets.offset.m_Item + Offsets.offset.m_iItemIDHigh,
                0xFFFFFFFF
            )

            memfuncs.ProcMemHandler.WriteInt(
                processHandle, active_weapon + Offsets.offset.m_nFallbackPaintKit, paint
            )
            memfuncs.ProcMemHandler.WriteFloat(
                processHandle, active_weapon + Offsets.offset.m_flFallbackWear, 0.001
            )

            # Force update (اختیاری - ممکنه لگ بده)
            # ...

    except Exception:
        pass