import asyncio
import os
import re
import time

from bleak import discover, BleakClient

from .exceptions import MirobotError, MirobotAlarm, MirobotReset, InvalidBluetoothAddressError


os_is_posix = os.name == 'posix'


def chunks(lst, n):
    """Yield successive n-sized chunks from lst.

    Parameters
    ----------
    lst : Collection
        An iterable of items.
    n : int
        The size of the chunks to split the list into.

    Returns
    -------
    result : Generator[List]
        A generator that yields each chunk of the list.
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


class BluetoothLowEnergyInterface:
    """
    An interface for talking to the low-energy Bluetooth extender module for the Mirobot.
    NOTE: This mode is inherently instable at the moment (@rirze, Thu 14 May 2020). Sometimes commands may not be parsed correctly, causing execution to fail on a misparsing error. While this happens rarely, users should be made aware of the potential exceptions that may arise. It is recommended to only use this connection when serial communication is unavailable.
    """
    def __init__(self, mirobot, address=None, debug=False, logger=None, autofindaddress=True):
        """

        Parameters
        ----------
        mirobot : `mirobot.base_mirobot.BaseMirobot`
            Mirobot object that this instance is attached to.
        address : str
            (Default value = None) Bluetooth address of the Mirobot's bluetooth extender module to connect to. If unknown, leave as `None` and this class will automatically scan and try to find the box on its own. If provided, it should be of the form `50:33:8B:L4:95:6X` (except on Apple products which use a format like `123JKDSF-F0E3-F96A-F0A3-64A68508A53C`)
        debug : bool
            (Default value = False) Whether to show debug statements in logger.
        logger : Logger
            (Default value = None) Logger instance to use for this class. Usually `mirobot.base_mirobot.BaseMirobot.logger`.
        autofindaddress : bool
            (Default value = True) Whether to automatically search for Mirobot's bluetooth module if `address` parameter is `None`.

        Returns
        -------
        class : `mirobot.bluetooth_low_energy_interface.BluetoothLowEnergyInterface`
        """
        self.mirobot = mirobot

        if logger is not None:
            self.logger = logger

        self._debug = debug

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self._run_and_get(self._ainit())

    async def _ainit(self, address=None, autofindaddress=True):
        # if address was not passed in and autofindaddress is set to true,
        # then autosearch for a bluetooth device
        if not address:
            if autofindaddress:
                self.address = await self._find_address()
                """ The default address to use when making connections. To override this on a individual basis, provide portname to each invocation of `BaseMirobot.connect`. """
                self.logger.info(f"Using Bluetooth Address \"{self.address}\"")
            else:
                self.logger.exception(InvalidBluetoothAddressError('Must either provide a Bluetooth address or turn on autodiscovery!'))
        else:
            self.address = address

        self.client = BleakClient(self.address, loop=self.loop)

    def _run_and_get(self, coro):
        return self.loop.run_until_complete(coro)

    @property
    def debug(self):
        """ Whether to show debug statements in the logger. """
        return self._debug

    @debug.setter
    def debug(self, value):
        """Set the new value for the `debug` property of `mirobot.bluetooth_low_energy_interface.BluetoothLowEnergyInterface`. Use as in `BluetoothLowEnergyInterface.setDebug(value)`.

        Parameters
        ----------
        value : bool
            New value for `debug`

        """
        self._debug = bool(value)

    async def _find_address(self):
        """ Try to find the Bluetooth Address automagically """
        devices = await discover()
        mirobot_bt = next((d for d in devices if d.name == 'QN-Mini6Axis'), None)
        if mirobot_bt is None:
            raise Exception('Could not find mirobot bt')

        return mirobot_bt.address

    def connect(self):
        """ Connect to the Bluetooth Extender Box """
        async def start_connection():
            connection = await self.client.connect()

            services = await self.client.get_services()
            service = services.get_service("0000ffe0-0000-1000-8000-00805f9b34fb")

            self.characteristics = [c.uuid for c in service.characteristics]

            return connection

        self.connection = self._run_and_get(start_connection())
    
    def disconnect(self):
        """ Disconnect from the Bluetooth Extender Box """
        async def async_disconnect():
            try:
                await self.client.disconnect()
            except AttributeError:
                '''
                File "/home/chronos/.local/lib/python3.7/site-packages/bleak/backends/bluezdbus/client.py", line 235, in is_connected
                    return await self._bus.callRemote(
                AttributeError: 'NoneType' object has no attribute 'callRemote'
                '''
                # don\t know why it happens, it shouldn't and doesn't in normal async flow
                # but if it complains that client._bus is None, then we're good, right...?
                pass

        self._run_and_get(async_disconnect())

    @property
    def is_connected(self):
        """ Whether this class is connected to the Bluetooth Extender Box """
        return self.connection

    def send(self, msg, disable_debug=False, terminator=None, wait=True, wait_idle=True):
        """

        Send a message to the Bluetooth Extender Box. Shouldn't be used by the end user.
        Parameters
        ----------
        msg : str
            The message/instruction to send. A `\\r\\n` will be appended to this message.
        disable_debug : bool
             (Default value = False) Whether to disable debug statements on `idle`-state polling.
        terminator : str
            (Default value = `None`) Dummy variable for this method. This implementation will always use `\\r\\n` as the line terminator.
        wait : bool
             (Default value = True) Whether to wait for the command to return a `ok` response.
        wait_idle :
             (Default value = True) Whether to wait for the Mirobot to be in an `Idle` state before returning.

        Returns
        -------
        msg : List[str] or bool
             If `wait` is `True`, then return a list of strings which contains message output.
             If `wait` is `False`, then return whether sending the message succeeded.

        """
        self.feedback = []
        self.ok_counter = 0
        self.disable_debug = disable_debug

        reset_strings = ['Using reset pos!']

        def matches_eol_strings(terms, s):
            for eol in terms:
                if s.endswith(eol):
                    return True
            return False

        def notification_handler(sender, data):
            data = data.decode()

            data_lines = re.findall(r".*[\r\n]{0,1}", data)
            for line in data_lines[:-1]:
                if self._debug and not self.disable_debug:
                    self.logger.debug(f"[RECV] {repr(line)}")

                if self.feedback and not self.feedback[-1].endswith('\r\n'):
                    self.feedback[-1] += line
                else:
                    if self.feedback:
                        self.feedback[-1] = self.feedback[-1].strip('\r\n')

                    if 'error' in line:
                        self.logger.error(MirobotError(line.replace('error: ', '')))

                    if 'ALARM' in line:
                        self.logger.error(MirobotAlarm(line.split('ALARM: ', 1)[1]))

                    if matches_eol_strings(reset_strings, line):
                        self.logger.error(MirobotReset('Mirobot was unexpectedly reset!'))

                    self.feedback.append(line)

                if self.feedback[-1] == 'ok\r\n':
                    self.ok_counter += 1

        async def async_send(msg):
            async def write(msg):
                for c in self.characteristics:
                    await self.client.write_gatt_char(c, msg)

            if wait:
                for c in self.characteristics:
                    await self.client.start_notify(c, notification_handler)

            for s in chunks(bytes(msg + '\r\n', 'utf-8'), 20):
                await write(s)

            if self._debug and not disable_debug:
                self.logger.debug(f"[SENT] {msg}")

            if wait:
                while self.ok_counter < 2:
                    # print('waiting...', msg, self.ok_counter)
                    await asyncio.sleep(0.1)

                if wait_idle:
                    # TODO: really wish I could recursively call `send(msg)` here instead of
                    # replicating logic. Alas...
                    orig_feedback = self.feedback

                    async def check_idle():
                        self.disable_debug = True
                        self.feedback = []
                        self.ok_counter = 0
                        await write(b'?\r\n')
                        while self.ok_counter < 2:
                            # print('waiting for idle...', msg, self.ok_counter)
                            await asyncio.sleep(0.1)
                        self.mirobot._set_status(self.mirobot._parse_status(self.feedback[0]))

                    await check_idle()

                    while self.mirobot.status.state != 'Idle':
                        # print(self.mirobot.status.state)
                        await check_idle()

                    # print('finished idle')
                    self.feedback = orig_feedback

                for c in self.characteristics:
                    await self.client.stop_notify(c)

        self._run_and_get(async_send(msg))

        if self.feedback:
            self.feedback[-1] = self.feedback[-1].strip('\r\n')

        # BUG:
        # the following bugs me so much, but I can't figure out why this is happening and needed:
        # Instant subsequent calls to `send_msg` hang, for some reason.
        # Like the second invocation doesn't start, it's gets stuck as `selector._poll` in asyncio
        # Putting a small delay fixes this but why...???
        if os_is_posix:
            time.sleep(0.1)

        return self.feedback
