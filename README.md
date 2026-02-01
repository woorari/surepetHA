# Sure Petcare HA for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)

A native Home Assistant integration for Sure Petcare devices, including the SureFlap Cat Flap and SureFeed Microchip Pet Feeder. This integration provides monitoring and control capabilities directly within Home Assistant.

## Features

- **SureFlap Support**: Monitor lock status and remotely lock/unlock your pet flaps.
- **SureFeed Support**: Track bowl status, last feeding time, and food metrics (portion sizes, remaining food).
- **Pet Tracking**: Keep track of your pets' locations (Inside/Outside).
- **Native Experience**: Fully integrated with the Home Assistant UI via Config Flow.

## Supported Platforms

- `sensor`: Battery levels, food weight, pet location, and device status.
- `lock`: Control and monitor your SureFlap devices.
- `select`: Change device modes.
- `button`: Manual triggers for specific actions.
- `device_tracker`: Track the location of your pets.

## Installation

### Method 1: HACS (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed.
2. Open **HACS** in your Home Assistant instance.
3. Click on the **three dots** in the top right corner and select **Custom repositories**.
4. Paste the URL of this repository into the **Repository** field.
5. Select **Integration** as the **Category**.
6. Click **Add**.
7. Find **Sure Petcare** in the HACS store and click **Download**.
8. Restart Home Assistant.

### Method 2: Manual Installation

1. Download the `custom_components/surepetcare_ha` folder from this repository.
2. Copy the folder to your Home Assistant `custom_components` directory (e.g., `/config/custom_components/surepetcare_ha`).
3. Restart Home Assistant.

## Configuration

1. After restarting, go to **Settings** > **Devices & Services**.
2. Click **Add Integration** in the bottom right corner.
3. Search for **Sure Petcare** and follow the on-screen instructions to log in with your Sure Petcare credentials.

## Services

### `surepetcare.set_pet_location`
Manually set the location of a pet.

| Field | Description |
|-------|-------------|
| `pet_id` | The ID of the pet to update. |
| `location` | The new location (1 for Inside, 2 for Outside/Away). |

## Disclaimer
This integration is not affiliated with or endorsed by Sure Petcare. It uses their unofficial API to provide Home Assistant support.
