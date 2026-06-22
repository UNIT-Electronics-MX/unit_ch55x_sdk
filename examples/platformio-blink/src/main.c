/*
 * PlatformIO blink example for the UNIT CH55x SDK.
 */

#include "system.h"
#include "gpio.h"
#include "delay.h"

#ifndef PIN_LED
#define PIN_LED P34
#endif

void main(void)
{
  CLK_config();
  DLY_ms(5);

  PIN_output(PIN_LED);

  while (1)
  {
    PIN_toggle(PIN_LED);
    DLY_ms(500);
  }
}
