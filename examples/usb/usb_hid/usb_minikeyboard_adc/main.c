/*
 * example - Derived Version
 *
 * ADC keyboard using resistor ladder on P1.5.
 *
 * Original work by Stefan Wagner
 * https://github.com/wagiminator/CH552-USB-CDC-OLED-Terminal
 *
 * Licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License.
 * To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/
 *
 * Modifications by Cesar Bautista for integration into Docker SDK
 */

#include "src/config.h"
#include "src/system.h"
#include "src/delay.h"
#include "src/gpio.h"
#include "src/usb_composite.h"

void USB_interrupt(void);
void USB_ISR(void) __interrupt(INT_NO_USB) {
  USB_interrupt();
}

enum {
  ADC_KEY_NONE = 0,
  ADC_KEY_UP,
  ADC_KEY_DOWN,
  ADC_KEY_LEFT,
  ADC_KEY_RIGHT,
  ADC_KEY_SPACE
};

// -----------------------------------------------------------------------------
// User configuration: assign action per switch (change order here)
// Example: swap SW1 and SW5 by exchanging SW1_KEY and SW5_KEY values.
// -----------------------------------------------------------------------------
// #define SW1_KEY ADC_KEY_UP
// #define SW2_KEY ADC_KEY_DOWN
// #define SW3_KEY ADC_KEY_LEFT
// #define SW4_KEY ADC_KEY_RIGHT
// #define SW5_KEY ADC_KEY_ENTER

#define SW1_KEY ADC_KEY_LEFT 
#define SW2_KEY ADC_KEY_UP
#define SW3_KEY ADC_KEY_DOWN
#define SW4_KEY ADC_KEY_RIGHT
#define SW5_KEY ADC_KEY_SPACE

// ADC thresholds (8-bit)
#define ADC_TH_NONE  245
#define ADC_TH_1_2    30
#define ADC_TH_2_3    80
#define ADC_TH_3_4   120
#define ADC_TH_4_5   180
#define ADC_TH_5_NP  230

// Resistor-ladder ADC key mapping (8-bit).
// If SW3/SW4 still overlap, tune ADC_TH_3_4.
static uint8_t adc_to_key(uint8_t adc_val) {
  if(adc_val >= ADC_TH_NONE) return ADC_KEY_NONE;
  if(adc_val <= ADC_TH_1_2)  return SW1_KEY;
  if(adc_val <= ADC_TH_2_3)  return SW2_KEY;
  if(adc_val <= ADC_TH_3_4)  return SW3_KEY;
  if(adc_val <= ADC_TH_4_5)  return SW4_KEY;
  if(adc_val <= ADC_TH_5_NP) return SW5_KEY;
  return ADC_KEY_NONE;
}

static void press_key(uint8_t key) {
  switch(key) {
    case ADC_KEY_UP:    KBD_press(KBD_KEY_UP_ARROW);    break;
    case ADC_KEY_DOWN:  KBD_press(KBD_KEY_DOWN_ARROW);  break;
    case ADC_KEY_LEFT:  KBD_press(KBD_KEY_LEFT_ARROW);  break;
    case ADC_KEY_RIGHT: KBD_press(KBD_KEY_RIGHT_ARROW); break;
    case ADC_KEY_SPACE: KBD_press(' ');                 break;
    default: break;
  }
}

static void release_key(uint8_t key) {
  switch(key) {
    case ADC_KEY_UP:    KBD_release(KBD_KEY_UP_ARROW);    break;
    case ADC_KEY_DOWN:  KBD_release(KBD_KEY_DOWN_ARROW);  break;
    case ADC_KEY_LEFT:  KBD_release(KBD_KEY_LEFT_ARROW);  break;
    case ADC_KEY_RIGHT: KBD_release(KBD_KEY_RIGHT_ARROW); break;
    case ADC_KEY_SPACE: KBD_release(' ');                 break;
    default: break;
  }
}
        
// Hold repeat: delay before first repeat and interval between repeats (ms)
// (not used - OS handles typematic repeat when key is held)

void main(void) {
  uint8_t adc_val;
  uint8_t key_now;
  uint8_t key_stable = ADC_KEY_NONE;
  uint8_t key_last_sample = ADC_KEY_NONE;
  uint8_t key_held = ADC_KEY_NONE;  // currently pressed key sent to HID

  CLK_config();
  DLY_ms(10);

  PIN_input(PIN_ADC);
  ADC_input(PIN_ADC);
  ADC_enable();

  HID_init();

  while (1) {
    // Single fast sample
    adc_val = (uint8_t)ADC_read();
    key_now = adc_to_key(adc_val);

    // Debounce: require 2 equal samples
    if(key_now == key_last_sample) {
      key_stable = key_now;
    } else {
      key_last_sample = key_now;
    }

    // Send press on down, release on up — OS handles repeat rate
    if(key_stable != key_held) {
      if(key_held != ADC_KEY_NONE) release_key(key_held);
      if(key_stable != ADC_KEY_NONE) press_key(key_stable);
      key_held = key_stable;
    }

    DLY_ms(5);
  }
}
