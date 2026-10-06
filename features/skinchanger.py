from functions import memfuncs
import time

# (itemDefinitionIndex or paintKit)
SKIN_MAP = {
    7:  433,   # AK-47 → Case Hardened
    9:  344,   # AWP → Dragon Lore
    16: 309,   # M4A4 → Howl
    60: 309,   # M4A1-S → Howl
    4:  38,    # Glock → Fade
    61: 653,   # USP-S → Kill Confirmed
}

def get_weapon_paint(item_def_index: int) -> int:
    return SKIN_MAP.get(item_def_index, 0)

def SkinChanger_Update(processHandle, clientBaseAddress, Offsets, Options):
    if not Options.get("EnableSkinChanger", False):
        return

    try:
        local_pawn = memfuncs.ProcMemHandler.ReadPointer(
            processHandle, clientBaseAddress + Offsets.offset.dwLocalPlayerPawn
        )
        if not local_pawn:
            return

        health = memfuncs.ProcMemHandler.ReadInt(processHandle, local_pawn + Offsets.offset.m_iHealth)
        if health <= 0:
            return

        # Only Active Weapon
        active_weapon = memfuncs.ProcMemHandler.ReadPointer(
            processHandle, local_pawn + Offsets.offset.m_pClippingWeapon
        )
        if not active_weapon:
            return

        item_def = memfuncs.ProcMemHandler.ReadShort(
            processHandle,
            active_weapon + Offsets.offset.m_AttributeManager +
            Offsets.offset.m_Item + Offsets.offset.m_iItemDefinitionIndex
        )

        paint = get_weapon_paint(item_def)
        if paint == 0:
            return

        current_paint = memfuncs.ProcMemHandler.ReadInt(
            processHandle, active_weapon + Offsets.offset.m_nFallbackPaintKit
        )

        if current_paint != paint:
            # force update
            memfuncs.ProcMemHandler.WriteUInt(
                processHandle,
                active_weapon + Offsets.offset.m_AttributeManager +
                Offsets.offset.m_Item + Offsets.offset.m_iItemIDHigh,
                0xFFFFFFFF  # or -1
            )
            memfuncs.ProcMemHandler.WriteInt(
                processHandle, active_weapon + Offsets.offset.m_nFallbackPaintKit, paint
            )
            memfuncs.ProcMemHandler.WriteFloat(
                processHandle, active_weapon + Offsets.offset.m_flFallbackWear, 0.001
            )

            # Force full update (maby lag)
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

    except Exception:
        pass