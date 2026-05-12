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
  ADC_KEY_ENTER
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

#define SW1_KEY ADC_KEY_UP
#define SW2_KEY ADC_KEY_RIGHT
#define SW3_KEY ADC_KEY_LEFT
#define SW4_KEY ADC_KEY_DOWN
#git sdefine SW5_KEY ADC_KEY_ENTER

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

static void send_key(uint8_t key) {
  switch(key) {
    case ADC_KEY_UP:    KBD_press(KBD_KEY_UP_ARROW);    KBD_release(KBD_KEY_UP_ARROW);    break;
    case ADC_KEY_DOWN:  KBD_press(KBD_KEY_DOWN_ARROW);  KBD_release(KBD_KEY_DOWN_ARROW);  break;
    case ADC_KEY_LEFT:  KBD_press(KBD_KEY_LEFT_ARROW);  KBD_release(KBD_KEY_LEFT_ARROW);  break;
    case ADC_KEY_RIGHT: KBD_press(KBD_KEY_RIGHT_ARROW); KBD_release(KBD_KEY_RIGHT_ARROW); break;
    case ADC_KEY_ENTER: KBD_press(KBD_KEY_RETURN);      KBD_release(KBD_KEY_RETURN);      break;
    default: break;
  }
}

void main(void) {
  uint8_t adc_val;
  uint16_t adc_acc;
  uint8_t i;
  uint8_t key_now;
  uint8_t key_stable = ADC_KEY_NONE;
  uint8_t key_last_sample = ADC_KEY_NONE;
  uint8_t stable_count = 0;
  uint8_t key_armed = 1;

  CLK_config();
  DLY_ms(10);

  PIN_input(PIN_ADC);
  ADC_input(PIN_ADC);
  ADC_enable();

  HID_init();

  while (1) {
    // Average 4 samples to reduce ADC noise.
    adc_acc = 0;
    for(i = 0; i < 4; i++) {
      adc_acc += (uint8_t)ADC_read();
      DLY_ms(1);
    }
    adc_val = (uint8_t)(adc_acc >> 2);

    key_now = adc_to_key(adc_val);

    // Debounce/filter: require 3 equal samples before accepting state.
    if(key_now == key_last_sample) {
      if(stable_count < 3) stable_count++;
    } else {
      key_last_sample = key_now;
      stable_count = 0;
    }
    if(stable_count >= 3) key_stable = key_now;

    // Edge trigger: send once when entering a valid key.
    if(key_stable == ADC_KEY_NONE) {
      key_armed = 1;
    } else if(key_armed) {
      send_key(key_stable);
      key_armed = 0;
    }

    DLY_ms(10);
  }
}
