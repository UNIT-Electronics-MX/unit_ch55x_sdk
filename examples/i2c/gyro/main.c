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

 #include "src/config.h"
 #include "src/system.h"
 #include "src/gpio.h"
 #include "src/delay.h"
 #include "src/i2c.h"
 #include "src/oled.h"
 #include <stdint.h>
 
 #define MPU6050_ADDR         0x68u
 #define MPU6050_PWR_MGMT_1   0x6Bu
 #define MPU6050_GYRO_XOUT_H  0x43u
 
 // Prototipos
 void MPU6050_init(void);
 void MPU6050_readGyro(int16_t *gx, int16_t *gy, int16_t *gz);
 void OLED_printInt(int16_t value);
 void OLED_printGyroLine(char axis, int16_t whole, int16_t frac, uint8_t newline);
 
 void main(void) {
     CLK_config();
     DLY_ms(5);
     I2C_init();
     MPU6050_init();
     OLED_init();
 
     while (1) {
         int16_t gx_raw, gy_raw, gz_raw;
         int16_t gx_int, gy_int, gz_int;
         int16_t gx_frac, gy_frac, gz_frac;
         int32_t temp_val;
 
         // Leer datos del giroscopio
         MPU6050_readGyro(&gx_raw, &gy_raw, &gz_raw);
 
         // Convertir a °/s usando escala 131 LSB/(°/s), sin float
         // Multiplicamos por 100 para mantener 2 decimales
         temp_val = (int32_t)gx_raw * 100 / 131;
         gx_int  = temp_val / 100;
         gx_frac = (temp_val >= 0 ? temp_val : -temp_val) % 100;
 
         temp_val = (int32_t)gy_raw * 100 / 131;
         gy_int  = temp_val / 100;
         gy_frac = (temp_val >= 0 ? temp_val : -temp_val) % 100;
 
         temp_val = (int32_t)gz_raw * 100 / 131;
         gz_int  = temp_val / 100;
         gz_frac = (temp_val >= 0 ? temp_val : -temp_val) % 100;
 
         OLED_clear();
         OLED_print("      Giroscopio     ");
         OLED_print("- - - - - - - - - - -\n");
 
         OLED_printGyroLine('X', gx_int, gx_frac, 1);
         OLED_printGyroLine('Y', gy_int, gy_frac, 1);
         OLED_printGyroLine('Z', gz_int, gz_frac, 0);
 
         // Espera antes de siguiente lectura
         DLY_ms(100);
     }
 }
 
 void MPU6050_init(void) {
     // Despertar al MPU6050
     I2C_start((uint8_t)(MPU6050_ADDR << 1));
     I2C_write(MPU6050_PWR_MGMT_1);
     I2C_write(0x00u);
     I2C_stop();
 }
 
 void MPU6050_readGyro(int16_t *gx, int16_t *gy, int16_t *gz) {
     // Lectura de registros de giroscopio
     I2C_start((uint8_t)(MPU6050_ADDR << 1));
     I2C_write(MPU6050_GYRO_XOUT_H);
     I2C_restart((uint8_t)((MPU6050_ADDR << 1) | 1u));
 
     *gx = (I2C_read((uint8_t)1) << 8) | I2C_read((uint8_t)1);
     *gy = (I2C_read((uint8_t)1) << 8) | I2C_read((uint8_t)1);
     *gz = (I2C_read((uint8_t)0) << 8) | I2C_read((uint8_t)0);
 
     I2C_stop();
 }

 void OLED_printInt(int16_t value) {
     uint16_t magnitude;
     uint16_t divisor = 10000;
     uint8_t started = 0;

     if (value < 0) {
         OLED_write('-');
         magnitude = (uint16_t)(-value);
     } else {
         magnitude = (uint16_t)value;
     }

     while (divisor > 1) {
         uint8_t digit = (uint8_t)(magnitude / divisor);
         if (digit || started) {
             OLED_write((char)('0' + digit));
             started = 1;
         }
         magnitude %= divisor;
         divisor /= 10;
     }
     OLED_write((char)('0' + magnitude));
 }

 void OLED_printGyroLine(char axis, int16_t whole, int16_t frac, uint8_t newline) {
     OLED_write(axis);
     OLED_print(": ");
     OLED_printInt(whole);
     OLED_write('.');
     OLED_write((char)('0' + (frac / 10)));
     OLED_write((char)('0' + (frac % 10)));
     if (newline) {
         OLED_write('\n');
     }
 }
