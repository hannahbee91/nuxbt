# CHANGELOG


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
