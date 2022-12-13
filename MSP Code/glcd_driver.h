/*
 * glcd_driver.h
 *
 *  Created on: Nov 24, 2022
 *      Author: Austin
 *
 *  Code largely copied from Lab 10 and modified to fit my needs.
 */

#ifndef GLCD_DRIVER_H_
#define GLCD_DRIVER_H_

#define CE  BIT0  // Chip Enable, P6.0
#define RST BIT6  // Reset, P6.6
#define DC  BIT7  // Data/Control, P6.7

#define GLCD_WIDTH 84
#define GLCD_HEIGHT 48

#define FRAME_WIDTH 64  // Video is 4:3


// Configure the SPI on UCB0
void SPI_init(void){
    EUSCI_B0->CTLW0 = 0x0001;   // reset UCB0
    EUSCI_B0->CTLW0 = 0x69C1;   // PH=0, PL=1, MSB first, Master, SPI, use SMCLK
    EUSCI_B0->BRW = 3;          // 3 MHz / 3 = 1 MHz
    EUSCI_B0->CTLW0 &= ~0x0001; // enable after config

    P1->SEL0 |= BIT5 | BIT6;    // use P1.5, P1.6 for UCB0
    P1->SEL1 |= ~(BIT5 | BIT6);

    P6->DIR |= CE | RST | DC;   // set P6.7, P6.6, P6.0 as output
    P6->OUT |= CE;              // CE high by default (idle high)
    P6->OUT |= ~RST;            // assert reset (ensure it's 0)
}


// Send data to the SPI Tx buffer
void SPI_write(unsigned char data){
    P6->OUT &= ~CE;                 // turn off CE - make ready for data
    EUSCI_B0->TXBUF = data;         // write data
    while(EUSCI_B0->STATW & BIT0);  // wait for transmit to finish
    P6->OUT |= CE;                  // turn CE back on
}


// Write data to GLCD as a command (configuration)
void GLCD_command_write(unsigned char data){
    P6->OUT &= ~DC;     // this write is a command
    SPI_write(data);    // write it
}


// Write data to GLCD as picture data
void GLCD_data_write(unsigned char data){
    P6->OUT |= DC;      // this write is data
    SPI_write(data);    // write it
}


// Move the cursor to bank y (0-5), column x (0-83)
void GLCD_setCursor(unsigned char x, unsigned char y){
    GLCD_command_write(0x80 | x);   // column
    GLCD_command_write(0x40 | y);   // bank
}


// Write 0 to the entire screen and reset the cursor position
void GLCD_clear(void){
    int i;
    for (i = 0; i < (GLCD_WIDTH * GLCD_HEIGHT / 8); i++)
        GLCD_data_write(0x00);
    GLCD_setCursor(0, 0);
}


// Initialize the PCD8544 controller
void GLCD_init(void){
    P6->OUT |= RST;             // hardware reset the GLCD controller
    GLCD_command_write(0x21);   // extended cmd. mode
    GLCD_command_write(0xB8);   // LCD operating voltage (for contrast)
    GLCD_command_write(0x04);   // temperature coefficient
    GLCD_command_write(0x14);   // 1:48 LCD bias
    GLCD_command_write(0x20);   // normal command mode
    GLCD_command_write(0x0C);   // normal display mode
}


// Write a character from charset to GLCD, one column at a time
// Note that my chars are 4 wide instead of 6
void GLCD_putchar(unsigned char c){
    int i;
    for(i = 0; i < 4; i++)
        GLCD_data_write(charset[c][i]);
}


// Write a 96-char frame from the frames array.
void GLCD_putframe(int f){
    // Reset bank number and cursor position
    int bank = 0;
    GLCD_setCursor(0, 0);

    // Decode the RLEd frame (char index, length, char index, length...)
    // (Preserved for posterity)
//    unsigned char decFrame[96];
//    int d = 0;  // Current decFrame index
//    // For each pair of chars in the encoded frame:
//    int i; for(i=0; frames[f][i] != '\0'; i+=2){
//        // data = frames[f][i]
//        // repetitions = frames[f][i+1]
//        // Write data to decFrame as many times as the encoding says
//        int j; for(j=0; j < frames[f][i+1]; j++){
//            decFrame[d++] = frames[f][i];
//        }
//    }

    // Write the 96 chars of the frame
    int i; for (i = 0; i < 96; i++){
        GLCD_putchar(frames[f][i]);
        //GLCD_putchar(decFrame[i]);
        // Every 16th char, set cursor to next bank
        if (i % 16 == 15){
            //bank++;
            GLCD_setCursor(0, ++bank);
        }
    }
}


#endif /* GLCD_DRIVER_H_ */
