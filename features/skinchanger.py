import struct
from functions import memfuncs

# ==================== Skin Map ====================
# itemDefinitionIndex → paintKit
# می‌تونی هر اسکینی که می‌خوای اینجا اضافه کنی
SKIN_MAP = {
	7:   44,     # AK-47 → Case Hardened
	9:   344,    # AWP → Dragon Lore
	16:  309,    # M4A4 → Howl
	60:  445,    # M4A1-S → Hyper Beast
	4:   38,     # Glock → Fade
	61:  653,    # USP-S → Kill Confirmed
	1:   37,     # Deagle → Blaze
	32:  653,    # P2000 → Fire Elemental
	36:  404,    # P250 → Asiimov
	63:  269,    # CZ75 → Victoria
	3:   44,     # Five-SeveN → Case Hardened
	30:  179,    # Tec-9 → Nuclear Threat
	64:  12,     # R8 → Crimson Web

	# چاقوها (مثال)
	# 500: 38,  # Bayonet → Fade
	# 507: 38,  # Karambit → Fade
}

def get_weapon_paint(item_def_index: int) -> int:
	return SKIN_MAP.get(item_def_index, 0)


def GetEntityFromHandle(processHandle, ListEntries, handle):
	"""تبدیل Handle به آدرس واقعی Entity (همان روش ESP پروژه)"""
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


def SkinChanger_Update(processHandle, clientBaseAddress, Offsets, Options):
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

		health = memfuncs.ProcMemHandler.ReadInt(
			processHandle, local_pawn + Offsets.offset.m_iHealth
		)
		if health <= 0:
			return

		# ---------- Weapon Services ----------
		weapon_services = memfuncs.ProcMemHandler.ReadPointer(
			processHandle, local_pawn + Offsets.offset.m_pWeaponServices
		)
		if not weapon_services:
			return

		# ---------- Active Weapon Handle ----------
		active_weapon_handle = memfuncs.ProcMemHandler.ReadUInt(
			processHandle, weapon_services + Offsets.offset.m_hActiveWeapon
		)
		if not active_weapon_handle:
			return

		# ---------- Resolve Handle → Weapon Pointer ----------
		active_weapon = GetEntityFromHandle(processHandle, ListEntries, active_weapon_handle)
		if not active_weapon:
			return

		# ---------- Item Definition Index ----------
		item_def = memfuncs.ProcMemHandler.ReadShort(
			processHandle,
			active_weapon + Offsets.offset.m_AttributeManager +
			Offsets.offset.m_Item + Offsets.offset.m_iItemDefinitionIndex
		)

		paint = get_weapon_paint(item_def)
		if paint == 0:
			return

		# ---------- Current Paint Kit ----------
		current_paint = memfuncs.ProcMemHandler.ReadInt(
			processHandle, active_weapon + Offsets.offset.m_nFallbackPaintKit
		)

		if current_paint != paint:
			# ItemIDHigh = -1 (force update)
			memfuncs.ProcMemHandler.WriteUInt(
				processHandle,
				active_weapon + Offsets.offset.m_AttributeManager +
				Offsets.offset.m_Item + Offsets.offset.m_iItemIDHigh,
				0xFFFFFFFF
			)

			# Paint Kit
			memfuncs.ProcMemHandler.WriteInt(
				processHandle,
				active_weapon + Offsets.offset.m_nFallbackPaintKit,
				paint
			)

			# Wear (هرچقدر کمتر، تمیزتر)
			memfuncs.ProcMemHandler.WriteFloat(
				processHandle,
				active_weapon + Offsets.offset.m_flFallbackWear,
				0.001
			)

			# Seed (اختیاری)
			memfuncs.ProcMemHandler.WriteInt(
				processHandle,
				active_weapon + Offsets.offset.m_nFallbackSeed,
				0
			)

			# ---------- Force Full Update (ممکنه کمی لگ بده) ----------
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
			except:
				pass

	except Exception:
		pass