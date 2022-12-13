#include "msp.h"
#include "charset.h"        // Characters
#include "frames.h"         // Frames
#include "title_screen.h"   // Title screen
#include "glcd_driver.h"    // GLCD code from Lab 10

// Not using any other drivers to save space for more frames

#define FRAMERATE 15    // frames/sec, kinda - actually capped at around 9.77

#define SW2 BIT4

// frame index
int frame = 0;

/**
 * main.c
 */
void main(void)
{
	WDT_A->CTL = WDT_A_CTL_PW | WDT_A_CTL_HOLD;		// stop watchdog timer

	// Prepare SPI and GLCD
	SPI_init();
    GLCD_init();
    GLCD_clear();

    // Init Timer_A 0 (based on Listing 7.9 in book)
    PJ->SEL0 |= BIT0 | BIT1;
    CS->KEY = CS_KEY_VAL;
    CS->CTL2 |= CS_CTL2_LFXT_EN;
    while(CS->IFG & CS_IFG_LFXTIFG)
        CS->CLRIFG |= CS_CLRIFG_CLR_LFXTIFG;
    CS->CTL1 |= CS_CTL1_SELA_0;
    CS->CLKEN |= CS_CLKEN_REFOFSEL;
    CS->CTL1 &= ~(CS_CTL1_SELS_MASK | CS_CTL1_DIVS_MASK);
    CS->CTL1 |= CS_CTL1_SELS_2;
    CS->KEY = 0;
    // 16384 is one second the way this is configured
    TIMER_A0->CCR[0] = 16384 / FRAMERATE;
    TIMER_A0->CTL = TIMER_A_CTL_TASSEL_1 | TIMER_A_CTL_MC__STOP | TIMER_A_CTL_CLR | TIMER_A_CTL_IE;
    NVIC->ISER[0] = 1 << ((TA0_N_IRQn) & 31);

    // Prepare SW2 for interrupts
    P1->SEL0 &= ~SW2;
    P1->SEL1 &= ~SW2;
    P1->DIR &= ~SW2;
    P1->REN |= SW2;
    P1->OUT |= SW2;
    P1->IE  |= SW2;
    P1->IES |= SW2;
    P1->IFG &= ~SW2;
    NVIC->ISER[1] |= 0x8;
    __enable_irq();

    // Set up MP3 module (P4.0 - ground it to play track)
    P4->DIR |= BIT0;
    P4->OUT |= BIT0;

    // Draw title screen
    int i; for(i = 0; i < 84*6; i++)
        GLCD_data_write(titleScreen[i]);

    // Wait for an interrupt
    while(1);
}

void PORT1_IRQHandler(void){
    // SW2 - play - start timer
    if (P1->IFG & SW2){
        P1->IFG &= ~SW2;

        GLCD_clear();

        // momentarily ground the MP3 control pin to play
        P4->OUT &= ~BIT0;
        __delay_cycles(500000);
        P4->OUT |= BIT0;

        // start timer
        TIMER_A0->CTL |= TIMER_A_CTL_MC__UPDOWN;

        // debounce (technically unnecessary since timer
        // stops other interrupts for some reason)
        __delay_cycles(5000);
    }
}

// Interrupt for Timer_A 0 - 1 frame per timer cycle
void TA0_N_IRQHandler(void){
    TIMER_A0->CTL &= ~TIMER_A_CTL_IFG;
    // Stop at the end :)
    if (frame < 2183)
        GLCD_putframe(++frame);
}
