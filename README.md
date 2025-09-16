# jtracer

Read data from EPEver Tracer 3210AN solar charge controller via serial Modbus RS485 interface.

I made my own [cable](https://waldrain.github.io/pv#tracer-rs485-cable) using
the info gleaned on the [RS485 communication](https://waldrain.github.io/pv#tracer-rs485-communication).

It requires a [CP210x USB to UART Bridge Virtual COM Port (VCP) driver](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers).

## Configuration Attempt

Failed in the end.
I ended up using the EPEver Windows software, cf. the following chast logs with ChatGPT and Gemini:

- [Modbus library for EPEver](https://chatgpt.com/share/68c942dc-7918-8005-8208-98fe52c63e58)
- [Connect Epever Tracer to Windows Software](https://g.co/gemini/share/922daad79e30)
- [LiFePO4 Battery Charge Protection Settings](https://g.co/gemini/share/213652ecba59)

## Author

Jeremy Tammik,
[The Building Coder](http://thebuildingcoder.typepad.com),
[ADN](http://www.autodesk.com/adn)
[Open](http://www.autodesk.com/adnopen),
[Autodesk Inc.](http://www.autodesk.com)

## License

This sample is licensed under the terms of
the [MIT License](http://opensource.org/licenses/MIT).
Please see the [LICENSE](LICENSE) file for full details.

