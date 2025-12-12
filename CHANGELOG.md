# CHANGELOG


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
