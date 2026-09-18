# MGO Brain Linux Deployment Pack

This directory prepares a Debian/Raspberry-Pi-style Linux host for MGO Brain. It is not a vehicle wiring guide.

## Target layout

- code / virtualenv: `/opt/mgo-brain`
- configuration: `/etc/mgo-brain`
- runtime/history: `/var/lib/mgo-brain`
- systemd unit: `/etc/systemd/system/mgo-brain.service`
- optional Avahi service: `/etc/avahi/services/mgo-brain.service`

## Hostname / mDNS

If the Linux hostname is set to `mgo` and Avahi is running, the device is normally reachable on the local network as:

`http://mgo.local:8080/`

The Avahi file advertises the HTTP service. Hostname configuration is intentionally not changed automatically by this repository.

## Recommended commissioning sequence

1. install the project into `/opt/mgo-brain/.venv`;
2. copy reviewed config files to `/etc/mgo-brain`;
3. create `/var/lib/mgo-brain` owned by the service account;
4. copy `deployment/mgo-brain.env.example` to `/etc/mgo-brain/mgo-brain.env`;
5. run `mgo-doctor`;
6. install/enable the systemd unit;
7. optionally install Avahi and the service descriptor;
8. verify `/health` and the PWA before connecting factory CAN.

## CAN warning

The systemd service does not configure CAN bitrate or listen-only mode.

Factory CAN must be configured separately and verified **listen-only** before MGO Brain is allowed to open the interface.

Do not put guessed bitrate, CAN pins, termination or DBC mappings into production configuration.
