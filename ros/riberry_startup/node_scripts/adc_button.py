#!/usr/bin/env python3

import rospy
# riberry.com.i2c_base は、このスクリプトが動作する環境に
# インストールされている必要があります。
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
    """
    ADS7828 ADC センサーをI2C経由で読み取るためのクラス。
    """
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
        """
        指定されたチャンネルのADC値を読み取り、
        ボタンが押されているか (True) 押されていないか (False) を返します。
        エラー時は -1 を返します。
        """
        if not 0 <= channel <= 7:
            print(f"[ADS7828] エラー: チャンネルは0から7の間で指定してください (指定値: {channel})")
            return -1 # エラーを示す

        command_byte = self.channel_to_addr[channel]

        with self.lock:
            try:
                self.i2c.write([command_byte])
                data = self.i2c.read(2)
            except OSError as e:
                print(f'[ADS7828] I2C OS ERROR on channel {channel}: {e}')
                return -1 # エラー
            except Exception as e:
                print(f'[ADS7828] Error reading channel {channel}: {e}')
                return -1 # エラー

        value = (data[0] << 8) | data[1]

        # 元のロジック: 4095 のときに True (押されている)
        if value == 4095:
            return True
        else:
            return False

    def close(self):
        """ I2C接続を閉じます。 """
        if hasattr(self, 'i2c'):
            self.i2c.close()
            print(f"[ADS7828] I2C connection {self.i2c.path} closed.")

# --- 長押し・短押し（タップ）検出のためのヘルパークラス ---
class ButtonLongPress:
    """
    ボタンの短押し（タップ）と長押しを検出する状態マシン。

    状態:
    - STATE_RELEASED (0): ボタンは離されている
    - STATE_PRESSED (1): ボタンは押されている (長押し未検出)
    - STATE_LONG_PRESS (2): ボタンは長押し状態

    動作:
    - 離されている時: 0
    - 押された瞬間: 0
    - 押されている間 (長押し時間未満): 0
    - 離された瞬間 (長押し時間未満): 1 (短押し/タップ)
    - 押されている間 (長押し時間経過後): 2 (長押し)
    - 離された瞬間 (長押し状態から): 0
    """

    STATE_RELEASED = 0
    STATE_PRESSED = 1
    STATE_LONG_PRESS = 2

    def __init__(self, long_press_duration_sec=0.5):
        """
        :param long_press_duration_sec: 長押しとみなす時間 (秒)
        """
        self.state = self.STATE_RELEASED
        self.last_state_bool = False # 直前の update 時の物理的な状態
        self.press_start_time = None # プレスが開始された時刻
        self.long_press_duration = rospy.Duration(long_press_duration_sec)

    def update(self, current_state_bool):
        """
        現在のボタンの物理状態 (True=押されている, False=離されている) に基づいて
        状態マシンを更新し、パブリッシュすべき値 (0, 1, または 2) を返す。

        :param current_state_bool: ADCから読み取った現在の物理状態
        :return: 0 (Released / Waiting), 1 (Short Press Event), 2 (Long Press Hold)
        """
        now = rospy.Time.now()

        publish_value = 0 # デフォルトは 0 (Released)

        # --- 状態遷移ロジック ---

        # 立ち上がりエッジ (押された瞬間: Released -> Pressed)
        if current_state_bool and not self.last_state_bool:
            self.state = self.STATE_PRESSED
            self.press_start_time = now
            publish_value = 0 # 押されたが、まだ長押しか短押しか不明

        # 立ち下がりエッジ (離された瞬間: Pressed (any state) -> Released)
        elif not current_state_bool and self.last_state_bool:

            if self.state == self.STATE_PRESSED:
                # 長押しになる前に離された
                publish_value = 1 # 短押し（タップ）イベント

            elif self.state == self.STATE_LONG_PRESS:
                # 長押し状態から離された
                publish_value = 0

            self.state = self.STATE_RELEASED
            self.press_start_time = None

        # 状態変化なし (Pressed -> Pressed)
        elif current_state_bool and self.last_state_bool:
            # 押され続けている
            if self.state == self.STATE_PRESSED:
                # 通常プレス状態。長押しになったか判定
                elapsed = now - self.press_start_time
                if elapsed > self.long_press_duration:
                    # 長押し閾値を超えた
                    self.state = self.STATE_LONG_PRESS
                    publish_value = 2 # 長押し
                else:
                    # まだ長押しになっていない (待機中)
                    publish_value = 0

            elif self.state == self.STATE_LONG_PRESS:
                # すでに長押し状態
                publish_value = 2 # 長押しを継続

        # 状態変化なし (Released -> Released)
        elif not current_state_bool and not self.last_state_bool:
            self.state = self.STATE_RELEASED
            publish_value = 0

        # 最後に、現在の物理状態を保存
        self.last_state_bool = current_state_bool

        return publish_value

# --- メインの実行部分 ---
if __name__ == "__main__":
    rospy.init_node("adc_button")

    try:
        # I2Cアドレス 0x48 でADCを初期化
        adc = ADS7828(addr=0x48)
    except Exception as e:
        rospy.logerr(f"ADS7828の初期化に失敗しました: {e}")
        rospy.signal_shutdown("ADC初期化失敗")
        import sys
        sys.exit(1)

    button_pub = rospy.Publisher("/adc_button_state", UInt8MultiArray, queue_size=1)

    # 10Hz (100ms周期)
    rate = rospy.Rate(10)

    # 長押しと判定する時間 (秒)
    long_press_time_sec = 0.3

    num_channels = 5

    # 5つのチャンネル（ボタン）それぞれのための状態管理クラスを初期化
    button_handlers = [ButtonLongPress(long_press_duration_sec=long_press_time_sec) for _ in range(num_channels)]

    rospy.loginfo(f"ADCボタンノード（長押し/短押し対応）を開始しました。 (長押し時間: {long_press_time_sec}秒)")

    while not rospy.is_shutdown():
        msg = UInt8MultiArray()
        data = []

        for ch in range(num_channels):
            try:
                # adc.getValue(ch) は True (pressed), False (released), または -1 (error) を返す
                is_pressed = adc.getValue(ch)

                if is_pressed == -1: # getValueがエラーを返した場合
                    rospy.logwarn_throttle(5.0, f"チャンネル {ch} のADC値の読み取りに失敗しました。")
                    # エラー時は 0 (Released) として扱う
                    is_pressed = False

                # 検出器の状態を更新し、
                # パブリッシュする値 (0, 1, または 2) を取得
                publish_value = button_handlers[ch].update(is_pressed)
                data.append(publish_value)

            except Exception as e:
                # メインループでの予期せぬエラー
                rospy.logerr(f"チャンネル {ch} の処理中にエラー: {e}")
                data.append(0) # エラー時は 0 を追加

        msg.data = data
        button_pub.publish(msg)

        try:
            rate.sleep()
        except rospy.ROSInterruptException:
            # ノードがシャットダウンされる (例: Ctrl+C)
            rospy.loginfo("シャットダウン要求を受け取りました。")
            pass

    # クリーンアップ
    adc.close()
    rospy.loginfo("ADCボタンノードをシャットダウンしました。")
