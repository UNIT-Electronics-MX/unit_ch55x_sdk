// =============================================================
// ⚠️ AVISO IMPORTANTE:
// Este firmware usa un VID/PID seguro por defecto (no registrado).
// Para compatibilidad con Quartus (USB-Blaster), puedes activar
// el VID/PID oficial de Intel bajo tu propio riesgo.
//
// ✅ Recomendado: dejar USE_COMPATIBLE_VIDPID en 0 si vas a distribuir
// =============================================================

// Cambia a 1 para usar VID/PID de Altera (solo uso personal / pruebas)
// descriptor.h

#define USE_COMPATIBLE_VIDPID     1
#define USE_COMPATIBLE_STRINGS    1

#if USE_COMPATIBLE_VIDPID
#define USB_VID  0x09FB
#define USB_PID  0x6001
#else
#define USB_VID  0x16C0
#define USB_PID  0x05DC
#endif

#if USE_COMPATIBLE_STRINGS
__code uint8_t Prod_Des[] = {
	2 + 2*11, 0x03, 'U', 0, 'S', 0, 'B', 0, '-', 0, 'B', 0, 'l', 0, 'a', 0, 's', 0, 't', 0, 'e', 0, 'r', 0
};
__code uint8_t Manuf_Des[] = {
	2 + 2*6, 0x03, 'A', 0, 'l', 0, 't', 0, 'e', 0, 'r', 0, 'a', 0
};
#else
__code uint8_t Prod_Des[] = {
	2 + 2*8, 0x03, 'P', 0, 'r', 0, 'o', 0, 'g', 0, '-', 0, 'F', 0, 'P', 0, 'G', 0, 'A', 0
};
__code uint8_t Manuf_Des[] = {
	2 + 2*11, 0x03, 'C', 0, 'o', 0, 'c', 0, 'k', 0, 'e', 0, 't', 0, ' ', 0, 'N', 0, 'o', 0, 'v', 0, 'a', 0
};
#endif

__code uint8_t DevDesc[] = {
	0x12, 0x01, 0x00, 0x02,
	0x00, 0x00, 0x00, 0x08,
	USB_VID & 0xFF, USB_VID >> 8,
	USB_PID & 0xFF, USB_PID >> 8,
	0x00, 0x04,
	0x01, 0x02, 0x03,
	0x01
};
