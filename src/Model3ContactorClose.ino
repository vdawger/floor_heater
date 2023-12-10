/*

* Modified by Will Viana May 2022 to remove model S info and focus more on model 3 battery.
*
 * Modified by Bryan Inkster May 2022 to do basic decodes from Model 3 battery pack   **************************************
 copyright 2016 Jack Rickard and Collin Kidder.  GPL license.  Use it for whatever you like, but attribute it.

it relies heavily on Collin Kidder's due_can library http://github.com/collin80


*/

// REMOVED all pin usage.

// VOLTLOG ESP32 CANLITE
#define LED 5    // On board LED
#define OUT1 17     // OUT1 via U2
#define PRECHARGE 17 
#define STATUS1 16  // STATUS of U2
#define OUT2 19     // OUT2 via U3
#define SOLAR 19 // 
#define STATUS2 18  // STATUS of U2
#define CANRX GPIO_NUM_22 // Define CAN RX pin
#define CANTX GPIO_NUM_23 // Define CAN TX pin


#include <esp32_can.h>  //https://github.com/collin80/

template<class T> inline Print &operator <<(Print &obj, T arg) { obj.print(arg); return obj; } //Sets up serial streaming Serial<<someshit;
 

//*********GENERAL VARIABLE   DATA ******************

CAN_FRAME outframe;  //A structured variable according to due_can library for transmitting CAN data.

//Other ordinary variables
float Version=0.1;
uint16_t page=300;    //EEPROM page to hold variable data.  We save time by setting up a structure and saving a large block
int i;
unsigned long elapsedtime, time228,timestamp,startime, lastime, last_update_time;  //Variables to compare millis for timers
boolean debug=false;
boolean testing=false;
boolean contact=false;
boolean precharge_closed=false; // pre-charge contactor false if open, true if closed.
boolean precharge_was=false; // to only change pins when value changes
boolean solar_closed=false;
boolean solar_was=false;
boolean need_heat=false;
boolean battery_info=false; //show battery info
boolean safety = false;
uint8_t logcycle=0;
uint8_t Frame6F2counter=0;
uint8_t framecycle=0;
uint8_t contactor=1;
uint8_t heating_on_temp = 4; // Degrees in C to turn on heat
uint8_t heating_off_temp = 10; // degress in C to turn off heat
uint16_t transmitime=30;
uint16_t refresh_interval = 2000; // interval for refreshing in ms
float invertervoltage=0.0f;
float carvoltage=0.0f;
float minvolts;
float maxvolts;
float cutoff_maxvolts = 4.17;
float turnon_maxvolts = 3.9;
float mintemp=4;
float maxtemp;
float soc;
float cutoff_soc = 90.0;
float turnon_soc = 70.0;
float amps;
float volts;
uint8_t minvno;
uint8_t maxvno;
float cell[97];

//******* END OF GENERAL VARIABLE DATA***********



//********************SETUP FUNCTION*******I*********
/*
 * The SETUP function in the Arduino IDE simply lists items that must be performed prior to entering the main program loop.  In this case we initialize Serial 
 * communications via the USB port, set an interrupt timer for urgent outbound frames, zero our other timers, and load our EEPROM configuration data saved during the 
 * previous session.  If no EEPROM data is found, we initialize EEPROM data to default values
 * 
 */
void setup(){
  Serial.begin(115200);  //Initialize our USB port which will always be redefined as SerialUSB to use the Native USB port tied directly to the SAM3X processor.  
  lastime=startime=timestamp=last_update_time=millis();  //Zero our other timers
  initializeCAN();     
  delay(5000);

  /*
  pinMode(PRECHARGE, OUTPUT);
  pinMode(SOLAR, OUTPUT);
  */

  // Start opened:
  /*
  digitalWrite(SOLAR, HIGH);
  digitalWrite(PRECHARGE, HIGH);
*/

  Serial<<"\n\n Startup successful. Tesla Model 3 Battery Read Program "<<Version<<"\n\n";
  printMenu();    
}
   
//********************END SETUP FUNCTION*******I*********

//********************MAIN PROGRAM LOOP*******I*********

void loop(){ 
  if(millis()-lastime > transmitime){ // set for 30ms for the 221 message
    lastime=millis();  //Zero our timer

    if(contact){
      send221frame(); // this message causes the contacts to close, must be sent at 30mS interval or so.
    }

    // CONTINGENCIES: 
    // IF SOLAR IS ON (Closed)
    if(solar_closed && safety){
      // It gets TOO COLD
      if(mintemp < heating_on_temp){
        solar_closed = false; //don't charge when below 4degree C
        Serial.print("\n\nSolar turned OFF b/c temp too low\n\nNEED HEAT\n\n");
        need_heat = true;
      }
      // SINGLE cell over voltage: 
      if(maxvolts > cutoff_maxvolts){
        Serial.print("\n\nSingle Cell over max allowed. Shutting off solar.\n\n");
        solar_closed = false;
      }
      // SOC over voltage: 
      if(soc > cutoff_soc){
        Serial.print("\nSOC was above cutoff value. shutting off solar to batt\n");
        solar_closed = true;
      }
    }
    // if off, then restore if criteria are met:
    if(!solar_closed && safety){
      // Battery is warm enough again:
      if(mintemp > heating_off_temp){
        need_heat = false; 
        solar_closed = true; // charge again when battery is warm enough
        Serial.print("\n\nSolar turned back ON b/c temp high enough.\n\n");
      }
      // SOC low enough:
      if(soc < turnon_soc){
        solar_closed = true;
        Serial.print("\n\nSolar turned back on b/c battery SOC low enough.\n\n");
      }
      if(maxvolts < turnon_maxvolts){
        solar_closed = true;
        Serial.print("\n\nSolar turned back on b/c single cell below threshold.\n\n");
      }
    }


    // only refresh screen less frequently: 
    if(millis()-last_update_time > refresh_interval && battery_info){
      last_update_time = millis();
      printBattery();
    }

    // push GPIO to reflect booleans:
    //handle_pins();
  }         
}
//********************END MAIN PROGRAM LOOP*******I*********


// Handle all GPIO pins to match boolean state:
void handle_pins(void){
  Serial.println("handling pins.");
  /*
  if(precharge_closed != precharge_was){
    precharge_was = precharge_closed; //update new current
    // only update pins if value has changed
    if(precharge_closed){
      // close the precharge GPIO pin contactor:
      digitalWrite(PRECHARGE,LOW);
    }
    if(!precharge_closed){
      //open precharge GPIO pin contactor:
      digitalWrite(PRECHARGE,HIGH);
    }
  }
  
  if(solar_closed != solar_was){
    solar_was = solar_closed;
    if(solar_closed){
      // close solar GPIO pins
      digitalWrite(SOLAR_NEG, LOW);
      digitalWrite(SOLAR_POS, LOW);
    }
    if(!solar_closed){
      // open solar GPIO pins
      digitalWrite(SOLAR_NEG, HIGH);
      digitalWrite(SOLAR_POS, HIGH);
    }
  }
  */
}
  
 //********************USB SERIAL INPUT FROM KEYBOARD *******I*********
 /* These routines use an automatic interrupt generated by SERIALEVENT to process keyboard input any time a string terminated with carriage return is received 
  *  from an ASCII terminal program via the USB port.  The normal program execution is interrupted and the checkforinput routine is used to examine the incoming
  *  string and act on any recognized text.
  * 
  */
   
void serialEventRun(void) 
{
   //if (Serial.available())Serial.print((char)Serial.read());//checkforinput(); //If serial event interrupt is on USB port, go check for keyboard input 
   if (Serial.available())checkforinput();//checkforinput(); //If serial event interrupt is on USB port, go check for keyboard input 
   if(Serial.available())Serial.print((char)Serial.read());          
}


void checkforinput(){
  //Checks for input from Serial Port 1 indicating configuration items most likely.  Handle each case.

  if (Serial.available()){
    int inByte = Serial.read();
    switch (inByte){
      case '?':
        printMenu();
        break; 	
      case 'h':
        printMenu();
        break;
      case 'a':
        safety = (!safety);
        break;
      case 'A':
        safety = (!safety);
        break;
      case 'b':
        battery_info = (!battery_info);
        break;
      case 'B':
        battery_info = (!battery_info);
      case 'D':
        debug=(!debug);
        break;
      case 'd':
        debug=(!debug);
        break;
      case 'i':
        getInterval();
        break;
      case 'I':
        getInterval();
        break;
      case 'c':
          contact=(!contact);
          break;
      case 'C':
          contact=(!contact);
          break; 
      case 'p':
          precharge_closed=(!precharge_closed);
          break;
      case 'P':
          precharge_closed=(!precharge_closed);
          break;
      case 's':
          solar_closed=(!solar_closed);
          break;
      case 'S':
          solar_closed=(!solar_closed);
          break;
      }  
  } 
}


void getInterval()
{
	Serial<<"\n Enter the interval in ms between each CAN frame transmission : ";
  while(Serial.available() == 0){}               
  float V = Serial.parseFloat();	
  if(V>0){
    Serial<<V<<"CAN frame interval\n\n";
    transmitime=abs(V);
  }
}
       
//********************END USB SERIAL INPUT FROM KEYBOARD ****************


//******************** USB SERIAL OUTPUT TO SCREEN ****************
/*  These functions are used to send data out the USB port for display on an ASCII terminal screen.  Menus, received frames, or variable status for example
 *   
 */

void printMenu(){
  Serial<<"\f\n=========== Tesla Model 3 Battery Monitor Version "<<Version<<" ==============\n************ List of Available Commands ************\n\n";
  Serial<<"  ? or h  - Print this menu\n";
  Serial<<"  b - Toggle battery info display\n";
  Serial<<"  a - Toggle safety features\n";
  Serial<<"  c - Toggle contactor state - sends 0x221 frame\n";
  Serial<<"  d - toggles debug DISPLAY FRAMES to print CAN data traffic\n";Serial<<"  p - toggles precharge contactor closed or open\n";
  Serial<<"  i - set interval in ms for screen print \n";
  Serial<<"  s - toggles solar contactors \n";
 
 Serial<<"**************************************************************\n==============================================================\n"; 
}

void printFrame(CAN_FRAME *frame,int sent){ 
  char buffer[300];
  sprintf(buffer, "msgID 0x%03X; %02X; %; %02X; %02X; %02X; %02X; %02X; %02X  %02d:%02d:%02d.%04d\n", frame->id, frame->data.bytes[0], 
  frame->data.bytes[1],frame->data.bytes[2], frame->data.bytes[3], frame->data.bytes[4], frame->data.bytes[5], frame->data.bytes[6],
  frame->data.bytes[7], hours(), minutes(), seconds(), milliseconds());
  
   if(sent)Serial<<"Sent ";
    else Serial<<"Received ";       
   Serial<<buffer<<"\n";
}

void printBattery(){
  /* This function prints an ASCII statement out the SerialUSB port summarizing various data from program variables.  Typically, these variables are updated
  *  by received CAN messages that operate from interrupt routines. This routine also time stamps the moment at which it prints out.
  */
  char buffer[300];

  Serial<<"\n";
  Serial<<"Tesla Model 3 Battery Pack Monitor - http://evtv.me & Bryan Inkster & Will Viana \n\n";
  if (contact) {Serial.print("Contactors Requested Close");}
  if (!contact) {Serial.print("Contactors Requested Open");}

  Serial.print("  Contactors = ");  
    if (contactor==5){Serial.print("CLOSED ");}
    if (contactor==1){Serial.print("OPEN   ");}
    if (contactor==7){Serial.print("WELDED ");} 
    if (contactor==8){Serial.print("POS CL ");}
    if (contactor==9){Serial.print("NEG CL ");}
    if (contactor==4){Serial.print("OPENING");}
    if (contactor==2){Serial.print("CLOSING");}
       
  Serial.print(" ");
  Serial.print("     SOC = ");
  Serial.print(soc,1);
  Serial.print("KWh     Volts = ");      
  Serial.print(volts,1);
  Serial.print("     Amps = ");      
  Serial.println(amps,1);
  
  Serial.print("  max Cell No ");
  Serial.print(maxvno);
  Serial.print(" = ");       
  Serial.print(maxvolts,3);
  Serial.print("     min Cell No ");
  Serial.print(minvno);
  Serial.print(" = ");      
  Serial.print(minvolts,3);   

  Serial.print("     max Cell Temp = ");
  Serial.print(maxtemp,1);
  Serial.print("     min Cell Temp = ");
  Serial.print(mintemp,1);  

  Serial.print("\nSolar Contactors:   ");
    if (solar_closed) {Serial.print("CLOSED.");}
    if (!solar_closed) {Serial.print("OPEN.");}
  Serial.print("\nPrecharge Contactor:   ");
    if (precharge_closed) {Serial.print("CLOSED.");}
    if (!precharge_closed) {Serial.print("OPEN.");}
  Serial.print("\nSafety features: ");
  Serial.print(safety);
}


int milliseconds(void){
  int milliseconds = (int) (micros()/100) %10000 ;
  return milliseconds;
}

int seconds(void){
    int seconds = (int) (micros() / 1000000) % 60 ;
    return seconds;
}

int minutes(void){
    int minutes = (int) ((micros() / (1000000*60)) % 60);
    return minutes;
}
    
int hours(void){    
    int hours   = (int) ((micros() / (1000000*60*60)) % 24);
    return hours;
}  


//******************** END USB SERIAL OUTPUT TO SCREEN ****************


//******************** CAN ROUTINES ****************************************
/* This section contains CAN routines to send and receive messages over the CAN bus
 *  INITIALIZATION routines set up CAN and are called from program SETUP to establish CAN communications.
 *  These initialization routines allow you to set filters and interrupts.  On RECEIPT of a CAN frame, an interrupt stops execution of the main program and 
 *  sends the frame to the specific routine used to process that frame by Message ID. Once processed, the main program is resumed.
 *  
 */

void initializeCAN(){
  //Initialize CAN bus 0 or 1 and set filters to capture incoming CAN frames and route to interrupt service routines in our program.

  CAN0.setCANPins(CANRX, CANTX);
  Serial.print("Set CAN RX: ");
  Serial.print(CANRX);
  Serial.print(". SET CANTX: ");
  Serial.print(CANTX);
  Serial.print("\n");
  if (CAN0.begin(500000)) {
    Serial.println("Using CAN0 - initialization completed.\n");
    //CAN0.setNumTXBoxes(3);
    CAN0.setRXFilter(0, 0x332, 0x7FF, false);       //min/max cell volts and temps
    CAN0.setCallback(0, handle332frame);
    CAN0.setRXFilter(1, 0x20A, 0x7FF, false);       // contactor state
    CAN0.setCallback(1, handle20Aframe); 
    CAN0.setRXFilter(2, 0x401, 0x7FF, false);       //cell voltages
    CAN0.setCallback(2, handle401frame);
    CAN0.setRXFilter(3, 0x352, 0x7FF, false);       // SOC
    CAN0.setCallback(3, handle352frame);
    CAN0.setRXFilter(4, 0x132, 0x7FF, false);       // battery amps/volts
    CAN0.setCallback(4, handle132frame);  
    CAN0.setGeneralCallback(handleCANframe);     // handle non-specified         
  }
  else Serial.println("CAN0 initialization (sync) ERROR\n");
}   

void handleCANframe(CAN_FRAME *frame)
// handles received frames not specified above.
//If you add other specific frames, do a setRXFilter and CallBack mailbox for each and do a method to catch those interrupts after the fashion
//of this one.
{  
    //This routine basically just prints the general frame received IF debug is set.  Beyond that it does nothing.
    
    if(debug) printFrame(frame,0); //If DEBUG variable is 1, print the actual message frame with a time stamp showing the time received.      
}

//***********  Model 3 battery CAN call backs *****************************************************************************

void handle332frame(CAN_FRAME *frame)
//This routine handles CAN interrupts from 0x332 CAN frame  = max/min cell Volts and Temps
{   
  uint16_t wolts;
  uint8_t mux;
    mux=(frame->data.bytes[0]);  //check mux
    mux=mux&0x03;    
  if (mux==1)  // then pick out max/min cell volts
    {    
    wolts=(word(frame->data.bytes[1],frame->data.bytes[0]));
    wolts >>=2;
    wolts = wolts&0xFFF;  
    maxvolts=wolts/500.0f;

    wolts=(word(frame->data.bytes[3],frame->data.bytes[2]));
    wolts = wolts&0xFFF;  
    minvolts=wolts/500.0f;

    wolts=(frame->data.bytes[4]);
    maxvno=1+(wolts&0x007F);
    
    wolts=(frame->data.bytes[5]);
    minvno=1+(wolts&0x007F);  
    }


  if (mux==0)         // then pick out max/min temperatures
  {
    wolts=(byte(frame->data.bytes[2]));
    maxtemp=(wolts*0.5f)-40;    
    
    wolts=(byte(frame->data.bytes[3])); 
    mintemp=(wolts*0.5f)-40;    
  }
         
    if(debug)printFrame(frame,0); //If DEBUG variable is 1, print the actual message frame with a time stamp showing the time received.    
}


//***************************************************************************
void handle401frame(CAN_FRAME *frame)
//This routine handles CAN interrupts from 0x401 CAN frame = cell voltages
{
  uint16_t wolts;
  uint8_t mux;
  mux=(frame->data.bytes[0]);    //get mux
  //   mux=mux&0x03;
  wolts=(frame->data.bytes[1]);   //status byte must be 0x02A
  if (wolts==0x02A){
    wolts=(word(frame->data.bytes[3],frame->data.bytes[2]));
    cell[1+mux*3]=wolts/10000.0f;
      wolts=(word(frame->data.bytes[5],frame->data.bytes[4]));
    cell[2+mux*3]=wolts/10000.0f;
      wolts=(word(frame->data.bytes[7],frame->data.bytes[6]));
    cell[3+mux*3]=wolts/10000.0f;           
  }
}

//************************************************************************************************
void handle20Aframe(CAN_FRAME *frame)
//This routine handles CAN interrupts from 0x20A CAN frame  = contactor state
{   
  uint16_t wolts;

    wolts=(frame->data.bytes[1]);           //check mux
    contactor=wolts&0x0F;
}


//************************************************************************************************
void handle352frame(CAN_FRAME *frame)
//This routine handles CAN interrupts from 0x352 CAN frame  = state of charge SOC
{   
  uint16_t wolts;

    wolts=(word(frame->data.bytes[4],frame->data.bytes[5]));
    wolts >>=1;
    wolts = wolts&0x03FF;  
    soc=wolts/10.0f;
}


//************************************************************************************************
void handle132frame(CAN_FRAME *frame)
//This routine handles CAN interrupts from 0x132 CAN frame  = battery amps / volts
{   
  uint16_t wolts;
  int16_t wamps;
  
    wolts=(word(frame->data.bytes[1],frame->data.bytes[0]));  
    volts=wolts/100.0f;

    wamps=(word(frame->data.bytes[3],frame->data.bytes[2])); 
    amps=(wamps)/10.0f;  
}

// **************  SEND ROUTINES **********************//

void send221frame() {                   // causes contact closure
  outframe.id = 0x221;            // Set our transmission address ID
  outframe.length = 8;            // Data payload 8 bytes
  outframe.extended = 0;          // Extended addresses - 0=11-bit 1=29bi
  outframe.rtr=1;                 //No request
  outframe.data.bytes[0]=0x41;
  outframe.data.bytes[1]=0x11;  
  outframe.data.bytes[2]=0x01;
  outframe.data.bytes[3]=0x00;
  outframe.data.bytes[4]=0x00;
  outframe.data.bytes[5]=0x00;
  outframe.data.bytes[6]=0x20;
  outframe.data.bytes[7]=0x96;

  CAN0.sendFrame(outframe);    //Mail it  
  if(debug){ // print if debug is on  
    Serial.print("\nSENT: 221 frame.");
  };                 
}

//******************** END CAN ROUTINES ****************
