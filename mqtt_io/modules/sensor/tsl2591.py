"""
TSL2591 High Dynamic Range Digital Light Sensor
"""

from typing import cast

from ...types import CerberusSchemaType, ConfigType, SensorValueType
from . import GenericSensor

REQUIREMENTS = ("smbus2",)
CONFIG_SCHEMA: CerberusSchemaType = {
    "i2c_bus_num": dict(type="integer", required=True, empty=False),
    "chip_on": dict(type="integer", required=True, empty=False),
    "chip_calib": dict(type="integer", required=True, empty=False),
    "chip_diode1": dict(type="integer", required=True, empty=False),
    "chip_diode2": dict(type="integer", required=True, empty=False),
    "chip_pn_id": dict(type="integer", required=True, empty=False),
}


class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the TSL2591 sensor.
    """

    SENSOR_SCHEMA: CerberusSchemaType = {
        "type": dict(
            type="string",
            required=False,
            empty=False,
            default="lux",
            allowed=["raw_luminosity", "full_spectrum", "infrared", "visible", "lux"],
        )
    }

    def setup_module(self) -> None:
        from smbus2 import SMBus  # type: ignore

        self.bus = SMBus(self.config["i2c_bus_num"])
        self.on: int = self.bus.write_byte_data(self.config["chip_on"])
        self.calib: int = self.bus.write_byte_data(self.config["chip_calib"])
        self.diode1: int = self.bus.read_i2c_block_data(self.config["chip_diode1"])
        self.diode2: int = self.bus.read_i2c_block_data(self.config["chip_diode2"])
        self.pn_id: int = self.bus.read_byte_data(self.config["chip_pn_id"])
        #
        # # switch on
        # self.bus.write_byte_data(0x39, 0x00 | 0x80, 0x03)
        # # Gain at 1x and exposure at 402ms
        # self.bus.write_byte_data(0x39, 0x01 | 0x80, 0x02)
        #
        # self.diode1: int = self.bus.read_i2c_block_data(0x39, 0x0C | 0x80, 2)
        # self.diode2: int = self.bus.read_i2c_block_data(0x39, 0x0E | 0x80, 2)
        #self.pn_id: int = self.bus.read_byte_data(0x39, 0x8A)

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        """
        Get the raw_luminosity, full_spectrum, infrared, visible or lux value from the sensor
        """
        sens_type = sens_conf["type"]
        data_diode1 = self.diode1
        data_diode2 = self.diode2
        pn_id = self.pn_id
        eye_ir = data_diode1[1] * 256 + data_diode1[0]
        ir = data_diode2[1] * 256 + data_diode2[0]

        return cast(
            float,
            dict(
                raw_luminosity=(pn_id, data_diode1, data_diode2),
                full_spectrum=eye_ir,
                infrared=ir,
                visible=(eye_ir - ir),
                lux=(int(ir)/int(eye_ir)),
            )[sens_type],
        )
