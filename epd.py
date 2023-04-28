# *****************************************************************************
# * | File        :	  Pico_ePaper-2.9.py
# * | Author      :   Waveshare team
# * | Function    :   Electronic paper driver
# * | Info        :
# *----------------
# * | This version:   V1.0
# * | Date        :   2021-03-16
# # | Info        :   python demo
# -----------------------------------------------------------------------------
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

from machine import Pin, SPI
import framebuf
import utime
import enviro
import config

# Display resolution
EPD_WIDTH       = 128
EPD_HEIGHT      = 296

RST_PIN         = 20
DC_PIN          = 16   
CS_PIN          = 17
BUSY_PIN        = 21
# RST_PIN         = 12
# DC_PIN          = 8
# CS_PIN          = 9
# BUSY_PIN        = 13
WF_PARTIAL_2IN9 = [
    0x0,0x40,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x80,0x80,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x40,0x40,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x80,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0A,0x0,0x0,0x0,0x0,0x0,0x1,  
    0x1,0x0,0x0,0x0,0x0,0x0,0x0,
    0x1,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x22,0x22,0x22,0x22,0x22,0x22,0x0,0x0,0x0,
    0x22,0x17,0x41,0xB0,0x32,0x36,
]

class EPD_2in9_Landscape(framebuf.FrameBuffer):
    def __init__(self):
        enviro.logging.debug("Create EPD")
        self.reset_pin = Pin(RST_PIN, Pin.OUT)
        
        self.busy_pin = Pin(BUSY_PIN, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(CS_PIN, Pin.OUT)
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        
        self.lut = WF_PARTIAL_2IN9
        
        self.spi = SPI(0)
        self.spi.init(baudrate=4000_000)
        self.dc_pin = Pin(DC_PIN, Pin.OUT)
        
        self.buffer = bytearray(self.height * self.width // 8)
        super().__init__(self.buffer, self.height, self.width, framebuf.MONO_VLSB)
        self.init()

    def digital_write(self, pin, value):
        pin.value(value)

    def digital_read(self, pin):
        return pin.value()

    def delay_ms(self, delaytime):
        utime.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.spi.write(bytearray(data))

    def module_exit(self):
        self.digital_write(self.reset_pin, 0)

    # Hardware reset
    def reset(self):
        enviro.logging.debug("Reset EPD")
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(50) 
        self.digital_write(self.reset_pin, 0)
        self.delay_ms(2)
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(50)   

    def send_command(self, command):
        self.digital_write(self.dc_pin, 0)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([command])
        self.digital_write(self.cs_pin, 1)

    def send_data(self, data):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([data])
        self.digital_write(self.cs_pin, 1)
        
    def ReadBusy(self):
        enviro.logging.debug("e-Paper busy")
        while(self.digital_read(self.busy_pin) == 1):      #  0: idle, 1: busy
            self.delay_ms(10) 
        enviro.logging.debug("e-Paper busy release")  

    def TurnOnDisplay(self):
        self.send_command(0x22) # DISPLAY_UPDATE_CONTROL_2
        self.send_data(0xF7)
        self.send_command(0x20) # MASTER_ACTIVATION
        self.ReadBusy()

    def TurnOnDisplay_Partial(self):
        self.send_command(0x22) # DISPLAY_UPDATE_CONTROL_2
        self.send_data(0x0F)
        self.send_command(0x20) # MASTER_ACTIVATION
        self.ReadBusy()

    def SendLut(self):
        self.send_command(0x32)
        for i in range(0, 153):
            self.send_data(self.lut[i])
        self.ReadBusy()

    def SetWindow(self, x_start, y_start, x_end, y_end):
        self.send_command(0x44) # SET_RAM_X_ADDRESS_START_END_POSITION
        # x point must be the multiple of 8 or the last 3 bits will be ignored
        self.send_data((x_start>>3) & 0xFF)
        self.send_data((x_end>>3) & 0xFF)
        self.send_command(0x45) # SET_RAM_Y_ADDRESS_START_END_POSITION
        self.send_data(y_start & 0xFF)
        self.send_data((y_start >> 8) & 0xFF)
        self.send_data(y_end & 0xFF)
        self.send_data((y_end >> 8) & 0xFF)

    def SetCursor(self, x, y):
        self.send_command(0x4E) # SET_RAM_X_ADDRESS_COUNTER
        self.send_data(x & 0xFF)
        
        self.send_command(0x4F) # SET_RAM_Y_ADDRESS_COUNTER
        self.send_data(y & 0xFF)
        self.send_data((y >> 8) & 0xFF)
        self.ReadBusy()
        
    def init(self):
        enviro.logging.debug("Init EPD")
        # EPD hardware init start     
        self.reset()

        self.ReadBusy()   
        self.send_command(0x12)  #SWRESET
        self.ReadBusy()   

        self.send_command(0x01) #Driver output control      
        self.send_data(0x27)
        self.send_data(0x01)
        self.send_data(0x00)
    
        self.send_command(0x11) #data entry mode       
        self.send_data(0x07)

        self.SetWindow(0, 0, self.width-1, self.height-1)

        self.send_command(0x21) #  Display update control
        self.send_data(0x00)
        self.send_data(0x80)
    
        self.SetCursor(0, 0)
        self.ReadBusy()
        # EPD hardware init end
        return 0

    def display(self, image):
        if (image == None):
            return            
        self.send_command(0x24) # WRITE_RAM
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(image[i + j * self.height])   
        self.TurnOnDisplay()

    def display_Base(self, image):
        if (image == None):
            return   
        self.send_command(0x24) # WRITE_RAM
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(image[i + j * self.height])    
                
        self.send_command(0x26) # WRITE_RAM
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(image[i + j * self.height])      
                
        self.TurnOnDisplay()
        
    def display_Partial(self, image):
        if (image == None):
            return
            
        self.digital_write(self.reset_pin, 0)
        self.delay_ms(2)
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(2)   
        
        self.SendLut()
        self.send_command(0x37) 
        self.send_data(0x00)  
        self.send_data(0x00)  
        self.send_data(0x00)  
        self.send_data(0x00) 
        self.send_data(0x00)  
        self.send_data(0x40)  
        self.send_data(0x00)  
        self.send_data(0x00)   
        self.send_data(0x00)  
        self.send_data(0x00)

        self.send_command(0x3C) #BorderWavefrom
        self.send_data(0x80)

        self.send_command(0x22) 
        self.send_data(0xC0)   
        self.send_command(0x20) 
        self.ReadBusy()

        self.SetWindow(0, 0, self.width - 1, self.height - 1)
        self.SetCursor(0, 0)
        
        self.send_command(0x24) # WRITE_RAM
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(image[i + j * self.height])    
        self.TurnOnDisplay_Partial()

    def Clear(self, color):
        enviro.logging.debug("CleAR EPD")
        self.send_command(0x24) # WRITE_RAM
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(color)
        self.TurnOnDisplay()

    def sleep(self):
        enviro.logging.debug("Sleep EPD")
        self.send_command(0x10) # DEEP_SLEEP_MODE
        self.send_data(0x01)
        
        self.delay_ms(2000)
        self.module_exit()

    def add_water_sensor_to_buffer(self, label, start_x, sensor_value, threshold):
        print(sensor_value)
        outer_height = 100
        inner_max_height = 90
        outer_width = 50
        inner_width = 40
        start_y = 20
        inner_start_x = start_x + 5
        max_inner_start_y = start_y + 5 
        self.text(label + ":" + str(sensor_value), start_x, 10, 0x00)
        self.rect(start_x, start_y, outer_width, outer_height, 0x00)
        for y_axis_value in range(max_inner_start_y, max_inner_start_y + outer_height - 10):
            percentage = int(((y_axis_value - max_inner_start_y) / (outer_height - 10)) * 100)
            if percentage % 20 == 0:
                self.hline(start_x + 3, y_axis_value, outer_width - 6, 0x00)
            if percentage % 5 == 0:
                self.hline(start_x + 10, y_axis_value, outer_width - 20, 0x00)
        self.hline(start_x + 3, max_inner_start_y, outer_width - 6, 0x00)
        self.hline(start_x + 3, max_inner_start_y + outer_height - 10, outer_width - 6, 0x00)
        actual_height = int(sensor_value * inner_max_height / 100)
        actual_inner_start_y = inner_max_height - actual_height + max_inner_start_y
        self.fill_rect(inner_start_x, actual_inner_start_y , inner_width, actual_height, 0x00)
        actual_height = int(threshold * inner_max_height / 100)
        threshold_y = inner_max_height - actual_height + max_inner_start_y
        threshold_notch_size = 5
        self.hline(start_x - threshold_notch_size - 3, threshold_y, threshold_notch_size, 0x00)
    
    def display_info(self, reading_copy):
        #epd_.init()
        self.Clear(0xff)
        self.fill(0xff)
        self.rect(0, 0, 296, 128, 0x00)
        timestamp=enviro.helpers.datetime_string()
        self.text(timestamp[timestamp.find("T") + 1:-1], 5, 100, 0x00)
        if type(reading_copy) is str:
            self.text(reading_copy, 5, 25, 0x00)
        else:
            self.text("Temp: ", 5, 25, 0x00)
            self.text("Humi: ", 5, 40, 0x00)
            self.text("Pres:", 5, 55, 0x00)
            self.text("Lumi:", 5, 70, 0x00)
            self.add_water_sensor_to_buffer("A", 110, reading_copy.get("moisture_a"), config.moisture_target_a)
            self.add_water_sensor_to_buffer("B", 170, reading_copy.get("moisture_b"), config.moisture_target_b)
            self.add_water_sensor_to_buffer("C", 230, reading_copy.get("moisture_c"), config.moisture_target_c)
            self.rect(230, 20, 50, 100, 0x00)
            self.text(str(reading_copy.get("temperature")), 50, 25, 0x00)
            self.text(str(reading_copy.get("humidity")), 50, 40, 0x00)
            self.text(str(reading_copy.get("pressure")), 50, 55, 0x00)
            self.text(str(reading_copy.get("luminance")), 50, 70, 0x00)
            
            self.display(self.buffer)
            self.sleep()