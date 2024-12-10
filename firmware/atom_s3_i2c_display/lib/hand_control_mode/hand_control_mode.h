#ifndef ATOM_S3_HAND_CONTROL_MODE_H
#define ATOM_S3_HAND_CONTROL_MODE_H

#include <mode.h>
#include <atom_s3_lcd.h>
#include <atom_s3_i2c.h>

class HandControlMode : public Mode {
public:
  HandControlMode(AtomS3LCD &lcd, AtomS3I2C &i2c);
  void createTask(uint8_t xCoreID) override;

private:
  static HandControlMode* instance; /**< Singleton instance of HandControlMode. */
  AtomS3LCD &atoms3lcd;
  AtomS3I2C &atoms3i2c;

  static void task(void *parameter);
};

#endif // ATOM_S3_HAND_CONTROL_MODE_H
