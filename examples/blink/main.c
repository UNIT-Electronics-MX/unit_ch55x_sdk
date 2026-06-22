/*
 * example - Derived Version
 * 
 * Original work by Stefan Wagner
 * https://github.com/wagiminator/CH552-USB-CDC-OLED-Terminal
 *
 * Licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License.
 * To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/
 *
 * Modifications by Cesar Bautista for integration into Docker SDK
 */


#include "src/system.h" 
#include "src/gpio.h"  
#include "src/delay.h"  

#define PIN_LED P34 

void main(void)
{
  CLK_config();
  DLY_ms(5);

  PIN_output(PIN_LED);
  while (1)
  {
    // Toggle LED state every 500ms
    PIN_toggle(PIN_LED);
    DLY_ms(100);
  }
}