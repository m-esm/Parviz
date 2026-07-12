#!/bin/sh
# Pair AirPods to Parviz's Pi. Put the AirPods IN the case, LID OPEN,
# HOLD the case button until the light PULSES WHITE, then run this
# (ssh moshe@moshe-pi5-2gb.local 'sh parviz-sw/audio/pair_airpods.sh').
# Scans up to 60 s for a device named *AirPods*, then pairs, trusts,
# connects, and plays a test tone through them.
set -e
echo "scanning for AirPods (60 s)..."
bluetoothctl scan on > /dev/null 2>&1 &
SCAN=$!
MAC=""
i=0
while [ $i -lt 20 ]; do
  MAC=$(bluetoothctl devices | grep -i airpod | head -1 | awk '{print $2}')
  [ -n "$MAC" ] && break
  sleep 3; i=$((i+1))
done
kill $SCAN 2>/dev/null || true
bluetoothctl scan off > /dev/null 2>&1 || true
if [ -z "$MAC" ]; then
  echo "NOT FOUND: is the case light pulsing white? Is the case near the Pi?"
  exit 1
fi
echo "found $MAC; pairing..."
bluetoothctl pair "$MAC" || true
bluetoothctl trust "$MAC"
bluetoothctl connect "$MAC"
sleep 3
pactl list short sinks
SINK=$(pactl list short sinks | grep -i bluez | head -1 | awk '{print $2}')
if [ -n "$SINK" ]; then
  pactl set-default-sink "$SINK"
  echo "default sink -> $SINK; playing test tone..."
  pactl play-sample bell 2>/dev/null || speaker-test -t sine -f 440 -l 1 -s 1 2>/dev/null || true
  echo "PAIRED AND CONNECTED. If you heard the tone, we're done."
else
  echo "connected but no bluez sink appeared; check: pactl list short sinks"
fi
