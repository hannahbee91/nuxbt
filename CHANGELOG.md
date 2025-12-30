# CHANGELOG


## v3.1.1 (2025-12-30)

### Bug Fixes

- **macros**: Macros now properly implemented held inputs
  ([`aa47b54`](https://github.com/hannahbee91/nuxbt/commit/aa47b541ae16ba06af91775a61c5b0755888dc84))

* fix(macros): Macros now properly implemented held inputs

feat(webapp): Keybinds can now be customized for keyboard and gamepad input

feat(macros): Macros now support categories

fix(plugin): Toggling the plugin now uses `realpath` to ensure the proper python executable gets
  capabilities set

* fix(tests): Fixed frontend tests for new elements and layout


## v3.1.0 (2025-12-24)

### Features

- **macros**: Allow written macros to hold inputs
  ([`65bac14`](https://github.com/hannahbee91/nuxbt/commit/65bac14e87e250c9b3ed4398ad6607cb6e08a6b8))

Held inputs stay held down until nested inputs are completed

Holds work within loops, both written and with the loop settings of the webapp


## v3.0.1 (2025-12-17)

### Bug Fixes

- **ppa**: Fixed issues with launchpad builds ([#30](https://github.com/hannahbee91/nuxbt/pull/30),
  [`5570f6d`](https://github.com/hannahbee91/nuxbt/commit/5570f6d161b86d35a367fe889bf9a57582356611))

Using pbuilder locally helps me make sure these issues don't come back.


## v3.0.0 (2025-12-17)

### Features

- **gui**: Created a gui for launching ([#29](https://github.com/hannahbee91/nuxbt/pull/29),
  [`64c135a`](https://github.com/hannahbee91/nuxbt/commit/64c135a2f7418f25645da018a41828502e85457d))

* feat(gui)!: Created a gui for launching

GUI is callable with `nuxbt gui`

Created desktop file for launching from application launcher

Isolated bluetooth permissions

App no longer requires being called with sudo

Check and Toggle bluetooth modifications with check and toggle commands

Replaced previously missed nxbt calls with nuxbt calls

Moved web app secrets and ssl certs to user config directory

* chore(ppa): Added copyright to PPA version

* fix(gui): Built in process management

Fixed issue where webapp instances, if not explicitly stopped, would keep running in the background.

* fix(cli): Ignored false-positive error on setcap


## v2.0.0 (2025-12-16)

### Features

- **webapp**: Revamp the WebApp ([#26](https://github.com/hannahbee91/nuxbt/pull/26),
  [`72c30f1`](https://github.com/hannahbee91/nuxbt/commit/72c30f140de0d26eb0d36d4c33ecde8957dd93ba))

* feat(webapp)!: Revamp the WebApp

Uses React and Tailwind for a more modern appearance. Allows for looping a certain number of times,
  or until stopped Supports light and dark mode Hotkey ('r') for starting/stopping macro recording
  Passes along gamepad input (needs more testing) Offers users to report detected bugs directly to
  GitHub

* fix(ci): Fixed node version in ci

Never trust VSCode autocomplete

* fix(ci): Ensure templates directory exists in build environment

* fix(tests): Forgot to update new app page title

* fix(ci): Verified all PyTests actually pass locally


## v1.5.5 (2025-12-15)

### Bug Fixes

- **ci**: Fixed a duplicated line causing validation error
  ([#24](https://github.com/hannahbee91/nuxbt/pull/24),
  [`bd2435a`](https://github.com/hannahbee91/nuxbt/commit/bd2435a787120b05895ef0460c803a2da615155a))


## v1.5.4 (2025-12-15)

### Bug Fixes

- **ci**: Use app token for release workflow to allow push to protected branch
  ([#23](https://github.com/hannahbee91/nuxbt/pull/23),
  [`924b71d`](https://github.com/hannahbee91/nuxbt/commit/924b71dd9d9904f51fadc8df0f2fcc9635721409))


## v1.5.3 (2025-12-15)

### Bug Fixes

- **release**: Ensure next version is 1.5.3 ([#22](https://github.com/hannahbee91/nuxbt/pull/22),
  [`e4b925a`](https://github.com/hannahbee91/nuxbt/commit/e4b925aa46ab33367a668f518bdfdadba5f39d29))


## v1.5.1 (2025-12-15)

### Bug Fixes

- **build**: Fixed more missing dependencies for builds
  ([#21](https://github.com/hannahbee91/nuxbt/pull/21),
  [`cb99a58`](https://github.com/hannahbee91/nuxbt/commit/cb99a58d01a1d5fe0c38eb937ab449c499ebbfff))

Built versions did not properly enforce bluetooth requirements

### Chores

- **ppa**: Fixed automated PPA builds ([#20](https://github.com/hannahbee91/nuxbt/pull/20),
  [`ccdf1cb`](https://github.com/hannahbee91/nuxbt/commit/ccdf1cb0a849fb849d96cc035ab269e9ed6d82ec))

Also introduced best practices to .gitignore for debian builds


## v1.5.0 (2025-12-15)

### Bug Fixes

- **misc**: Fixed added debug file again [skip ci]
  ([`677e9de`](https://github.com/hannahbee91/nuxbt/commit/677e9de9d0849c7bc4a7fd2c9d3ac99cabc0ba84))

- **misc**: Got rid of inadvertently added file
  ([`4ddc05b`](https://github.com/hannahbee91/nuxbt/commit/4ddc05b2d344da68885a30d2c95a848ebba1ce75))

### Features

- **webapp**: Allow Saving of Macros ([#19](https://github.com/hannahbee91/nuxbt/pull/19),
  [`761cbb8`](https://github.com/hannahbee91/nuxbt/commit/761cbb83bbfd13ed7c62388be6875f880a39a821))

Macros can now be saved and loaded for future use Macros are stored under `~/.config/nuxbt/macros`
  You can write macros in any editor and save them to config directory and they will be loaded in at
  next launch of the app Closes #18


## v1.4.1 (2025-12-13)

### Bug Fixes

- **releases**: Fixed debsource workflow dependencies
  ([#16](https://github.com/hannahbee91/nuxbt/pull/16),
  [`c4af224`](https://github.com/hannahbee91/nuxbt/commit/c4af22400981b23d26e53d4c1d7b986abc244284))


## v1.4.0 (2025-12-13)

### Features

- **vagrant**: Vagrant now uses PPA to install ([#15](https://github.com/hannahbee91/nuxbt/pull/15),
  [`4ad2192`](https://github.com/hannahbee91/nuxbt/commit/4ad219241e622383fd068040f0096d408278e734))

* feat(vagrant): Vagrant now uses PPA to install

* fix(ci): Fixed dependencies in PPA source

* fix(ci): Fixed syntax of workflow


## v1.3.2 (2025-12-13)

### Bug Fixes

- **ppa**: Fixed issues with missing original tarball
  ([#13](https://github.com/hannahbee91/nuxbt/pull/13),
  [`50801b8`](https://github.com/hannahbee91/nuxbt/commit/50801b8b031e7447fdc66e84b0d029d6891362b7))


## v1.3.1 (2025-12-13)

### Bug Fixes

- **ppa**: Fixed ppa workflow ([#12](https://github.com/hannahbee91/nuxbt/pull/12),
  [`4cb7223`](https://github.com/hannahbee91/nuxbt/commit/4cb7223a9e4cb201b73a5ba181a64e0f840ad2f7))


## v1.3.0 (2025-12-13)

### Features

- **releases**: Automatically publish new versions to ppa
  ([#11](https://github.com/hannahbee91/nuxbt/pull/11),
  [`1dd2baa`](https://github.com/hannahbee91/nuxbt/commit/1dd2baa57e69d821c2ac7551e71c7cda8fb3dd24))


## v1.2.2 (2025-12-12)

### Bug Fixes

- **releases**: Fixed the release and deb package dependencies to target 3.12
  ([#10](https://github.com/hannahbee91/nuxbt/pull/10),
  [`bc95561`](https://github.com/hannahbee91/nuxbt/commit/bc95561ffe67475f2a3e1781b39540abf31d4059))


## v1.2.1 (2025-12-12)

### Bug Fixes

- **releases**: Fixed permissions for uploading build artifacts
  ([#9](https://github.com/hannahbee91/nuxbt/pull/9),
  [`ec41594`](https://github.com/hannahbee91/nuxbt/commit/ec4159493bfb3ae6eb364f414c249e965e7236ee))


## v1.2.0 (2025-12-12)

### Features

- **releases**: Releases now build DEB and RPM files
  ([#8](https://github.com/hannahbee91/nuxbt/pull/8),
  [`06f5c5a`](https://github.com/hannahbee91/nuxbt/commit/06f5c5a7edc1767b7be2388e5a47a8021e410316))


## v1.1.2 (2025-12-12)

### Bug Fixes

- **bluetooth**: Fixed issues with reliably connecting
  ([#7](https://github.com/hannahbee91/nuxbt/pull/7),
  [`471380b`](https://github.com/hannahbee91/nuxbt/commit/471380bbb2ab1c65cfc1deed15bf2b0526b47486))

Introduced a bluez agent to silently accept pairing requests on the host

Also made some other minor changes


## v1.1.1 (2025-12-12)

### Bug Fixes

- **bug**: Fixed missing package files in manifest
  ([#6](https://github.com/hannahbee91/nuxbt/pull/6),
  [`924c0bc`](https://github.com/hannahbee91/nuxbt/commit/924c0bc3b8178771a161e73e84b62e9b99d1c708))

### Testing

- Added tests and updated documentation ([#5](https://github.com/hannahbee91/nuxbt/pull/5),
  [`07d192a`](https://github.com/hannahbee91/nuxbt/commit/07d192a66ae21a3065c3549d6e00b71e98cee217))

* build: Ensure non-core changes are not counted as new versions

* test(tui): Added tests to the TUI

* docs: Updated readme and vagrant with published PyPi package

* docs: Added CoC and Contributing

* docs: Updated readme

* docs: Update plans and screenshots

* fix(tests): Fixed headless TUI tests


## v1.1.0 (2025-12-12)

### Bug Fixes

- **ci**: Fixed how versions are updated ([#4](https://github.com/hannahbee91/nuxbt/pull/4),
  [`73013ee`](https://github.com/hannahbee91/nuxbt/commit/73013eee542d14d11295649cebfa6fcc0f88aad3))

Also fixed release dependencies


## v0.1.0 (2025-12-12)

### Bug Fixes

- **ci**: Fixed bump_version access ([#3](https://github.com/hannahbee91/nuxbt/pull/3),
  [`27eea3c`](https://github.com/hannahbee91/nuxbt/commit/27eea3cae37d2c22bbfda4abe16663d797025877))

### Features

- Migrate to poetry ([#2](https://github.com/hannahbee91/nuxbt/pull/2),
  [`ae9456f`](https://github.com/hannahbee91/nuxbt/commit/ae9456f185458475f4520170e793c0ae5550b4a7))

Also updated tooling and workflows for proper release flows


## v1.0.1 (2025-12-11)

### Features

- Upgrade cli to use click ([#1](https://github.com/hannahbee91/nuxbt/pull/1),
  [`2dfcc42`](https://github.com/hannahbee91/nuxbt/commit/2dfcc42d49fc737ee6916e6d75c55e9db9735810))

* feat: Upgrade cli to use click

chore: Add test suite

* chore: Replace eventlet (deprecated) with uvicorn
