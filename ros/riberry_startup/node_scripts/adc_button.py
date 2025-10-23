#!/usr/bin/env python3

import rospy
from riberry.com.i2c_base import I2CBase
from std_msgs.msg import UInt8MultiArray

ADC_CH0_INTERNAL = 0x8C # CH1
ADC_CH1_INTERNAL = 0xCC # CH2
ADC_CH2_INTERNAL = 0x9C # CH3
ADC_CH3_INTERNAL = 0xDC # CH4
ADC_CH4_INTERNAL = 0xAC # CH5
ADC_CH5_INTERNAL = 0xEC # CH6
ADC_CH6_INTERNAL = 0xBC # CH7
ADC_CH7_INTERNAL = 0xFC # CH8

class ADS7828(I2CBase):
    def __init__(self, addr):
        try:
            super().__init__(i2c_addr=addr)
        except ValueError as e:
            print(f"[ADS7828] 初期化エラー: {e}")
            print("サポートされていないデバイスか、I2Cバスのセットアップに失敗しました。")
            raise

        self.channel_to_addr = [
            ADC_CH0_INTERNAL, ADC_CH1_INTERNAL,
            ADC_CH2_INTERNAL, ADC_CH3_INTERNAL,
            ADC_CH4_INTERNAL, ADC_CH5_INTERNAL,
            ADC_CH6_INTERNAL, ADC_CH7_INTERNAL
        ]

        print(f"[ADS7828] アドレス {hex(addr)} で {self.device_type} 上の {self.i2c.path} を初期化しました。")

    def getValue(self, channel):
        if not 0 <= channel <= 7:
            print(f"[ADS7828] エラー: チャンネルは0から7の間で指定してください (指定値: {channel})")
            return -1 # または ValueErrorを発生させる

        command_byte = self.channel_to_addr[channel]

        with self.lock:
            try:
                self.i2c.write([command_byte])
                data = self.i2c.read(2)
            except OSError as e:
                print(f'[ADS7828] I2C OS ERROR on channel {channel}: {e}')
                return -1
            except Exception as e:
                print(f'[ADS7828] Error reading channel {channel}: {e}')
                return -1

        value = (data[0] << 8) | data[1]
        if value ==4095:
            return True
        else:
            return False

    def close(self):
        if hasattr(self, 'i2c'):
            self.i2c.close()
            print(f"[ADS7828] I2C connection {self.i2c.path} closed.")

if __name__ == "__main__":
    rospy.init_node("adc_button")
    adc = ADS7828(addr=0x48)
    button_pub = rospy.Publisher("/adc_button_state", UInt8MultiArray, queue_size=1)
    rate = rospy.Rate(10)
    while not rospy.is_shutdown():
        msg = UInt8MultiArray()
        data = []
        for ch in range(5):
            data.append(adc.getValue(ch))
        msg.data = data
        button_pub.publish(msg)
        rate.sleep()
