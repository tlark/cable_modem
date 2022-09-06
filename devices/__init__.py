from hnap import HNAPDevice


def create_device(device_id: str) -> HNAPDevice:
    if device_id == 'arris':
        from devices.arris import ArrisDevice

        return ArrisDevice(device_id)
    elif device_id == 'motorola':
        from devices.motorola import MotorolaDevice

        return MotorolaDevice(device_id)
    else:
        raise ValueError('No device for id={}'.format(device_id))
