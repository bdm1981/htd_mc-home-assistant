# HTD Lync Series integration for Home Assistant

Home Assistant component for [Home Theater Direct (HTD)](https://www.htd.com/Products/Whole-House-Audio/Lync) Lync whole house audio systems.

![Screenshot](https://github.com/bdm1981/htd_mc-home-assistant/blob/master/home-assistant-screenshot.png?raw=true)

## Installation steps

1. Download the 4 files (`__init__.py`, `htd_mc.py`, `media_player.py`, `manifest.json`) from this repo and place them into your `custom_components/htd_mc` folder.
2. Update your configuration.yaml to include the following. Set the source name to `hidden` for any sources you don't want to show up in Home Assistant.
   ```yaml
   htd_mc:
     - host: 192.168.1.123
       port: 10006
       zones:
         - Kitchen
         - Dining Room
         - Living Room
       sources:
         - hidden # add a hidden entry for any disabled zones
         - Chrome Cast
         - FM/AM
         - 4
         - 5
         - 6
         - 7
         - 8
         - 9
         - 10
         - 11
         - 12
         - 13
         - 14
         - 15
         - 16
   ```
3. Restart Home Assistant

## Code Credits

- https://github.com/whitingj/mca66
- https://github.com/steve28/mca66
- http://www.brandonclaps.com/?p=173
