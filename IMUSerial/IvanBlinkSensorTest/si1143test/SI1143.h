#ifndef SI1143_h
#define SI1143_h

#define IR_ADDRESS 0x5A

// register addresses
#define PART_ID        0x00
#define REV_ID         0x01
#define SEQ_ID         0x02  //Si114x-A11 (MAJOR_SEQ=1, MINOR_SEQ=1)
#define INT_CFG        0x03
#define IRQ_ENABLE     0x04
#define IRQ_MODE1      0x05
#define IRQ_MODE2      0x06
#define HW_KEY         0x07

#define MEAS_RATE      0x08
#define ALS_RATE       0x09
#define PS_RATE        0x0A

#define ALS_LOW_TH0    0x0B
#define ALS_LOW_TH1    0x0C
#define ALS_HI_TH0     0x0D
#define ALS_HI_TH1     0x0E

#define PS_LED21       0x0F
#define PS_LED3        0x10

#define PS1_TH0        0x11
#define PS1_TH1        0x12
#define PS2_TH0        0x13
#define PS2_TH1        0x14
#define PS3_TH0        0x15

#define PS3_TH1        0x16
#define PARAM_WR       0x17
#define COMMAND        0x18

#define RESPONSE       0x20
#define IRQ_STATUS     0x21

#define ALS_VIS_DATA0  0x22
#define ALS_VIS_DATA1  0x23
#define ALS_IR_DATA0   0x24
#define ALS_IR_DATA1   0x25

#define PS1_DATA0      0x26
#define PS1_DATA1      0x27
#define PS2_DATA0      0x28
#define PS2_DATA1      0x29
#define PS3_DATA0      0x2A
#define PS3_DATA1      0x2B


#define AUX_DATA0      0x2C
#define AUX_DATA1      0x2D

#define PARAM_RD       0x2E
#define CHIP_STAT      0x30
#define ANA_IN_KEY     0x3B

// ram addresses

#define I2C_ADDR                  0x00
#define CHLIST                    0x01
#define PSLED12_SELECT            0x02  
#define PSLED3_SELECT             0x03
#define PS_ENCODING               0x05
#define ALS_ENCODING              0x06
#define PS1_ADCMUX                0x07
#define PS2_ADCMUX                0x08
#define PS3_ADCMUX                0x09
#define PS_ADC_COUNTER            0x0A
#define PS_ADC_GAIN               0x0B
#define PS_ADC_MISC               0x0C
#define ALS_IR_ADCMUX             0x0E
#define AUX_ADCMUX                0x0F
#define ALS_VIS_ADC_COUNTER       0x10
#define ALS_VIS_ADC_GAIN          0x11
#define ALS_VIS_ADC_MISC          0x12
#define ALS_HYST                  0x16
#define PS_HYST                   0x17
#define PS_HISTORY                0x18
#define ALS_HISTORY               0x19
#define ADC_OFFSET                0x1A
#define LED_REC                   0x1C
#define ALS_IR_ADC_COUNTER        0x1D
#define ALS_IR_ADC_GAIN           0x1E
#define ALS_IR_ADC_MISC           0x1F

#endif