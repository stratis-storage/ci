---
name: bump-dbus-revision
description: Bump the stratisd D-Bus interface revision version number. Creates new interface module directories, updates registrations, updates stratisd.conf, bumps Cargo.toml minor version, builds with sim engine, and regenerates introspection data. Use when the user asks to bump the D-Bus revision, bump the version, or add a new revision.
---

# Bump D-Bus Revision

When the user asks to bump the D-Bus revision version in stratisd, follow this workflow. You should prompt the user for the location of the stratisd repository.

All steps below use these variables (determine them in Step 1):
- `CURRENT` = current Cargo.toml minor version (the current D-Bus revision number)
- `NEW` = CURRENT + 1 (the new D-Bus revision number)
- `MAJOR` = current Cargo.toml major version (currently `3`)

## Step 1: Determine version numbers

1. Read `Cargo.toml` at the project root to extract the current version (format: `MAJOR.MINOR.PATCH`).
2. Set `CURRENT = MINOR`, `NEW = MINOR + 1`.
3. Update the version in `Cargo.toml` from `MAJOR.CURRENT.PATCH` to `MAJOR.NEW.0` (bump minor, reset patch to 0).

## Step 2: Create new D-Bus interface module files

For each of the 5 interface types below, copy all files from the latest revision directory to a new directory, then in each copied file:
- Replace the struct name: e.g., `BlockdevR{CURRENT}` -> `BlockdevR{NEW}` (all occurrences)
- Replace the interface annotation revision: e.g., `blockdev.r{CURRENT}` -> `blockdev.r{NEW}`
- **Do NOT** change any import paths — they should continue importing from the same earlier revisions they already reference

### 2a. Blockdev

Copy `src/dbus/blockdev/blockdev_{MAJOR}_{CURRENT}/mod.rs` to `src/dbus/blockdev/blockdev_{MAJOR}_{NEW}/mod.rs`.

### 2b. Filesystem

Copy `src/dbus/filesystem/filesystem_{MAJOR}_{CURRENT}/mod.rs` to `src/dbus/filesystem/filesystem_{MAJOR}_{NEW}/mod.rs`.

### 2c. Pool

Copy **only** `src/dbus/pool/pool_{MAJOR}_{CURRENT}/mod.rs` to `src/dbus/pool/pool_{MAJOR}_{NEW}/mod.rs`.

Do **NOT** copy `methods.rs` or `props.rs` — the new revision reuses the previous revision's implementations. In the new `mod.rs`, replace the local sub-module declarations and re-exports:
```rust
mod methods;
mod props;

pub use methods::{...};
pub use props::{...};
```
with imports from the previous revision:
```rust
use crate::dbus::pool::pool_{MAJOR}_{CURRENT}::{...the same symbols...};
```
Keep all other imports (from older revisions like pool_3_0, pool_3_1, etc.) unchanged.

### 2d. Manager

Copy **only** `src/dbus/manager/manager_{MAJOR}_{CURRENT}/mod.rs` to `src/dbus/manager/manager_{MAJOR}_{NEW}/mod.rs`.

Do **NOT** copy `methods.rs`. In the new `mod.rs`, replace the local sub-module declaration and re-export:
```rust
mod methods;

pub use methods::{...};
```
with an import from the previous revision:
```rust
use crate::dbus::manager::manager_{MAJOR}_{CURRENT}::{...the same symbols...};
```

### 2e. Report

Copy `src/dbus/manager/report_{MAJOR}_{CURRENT}/mod.rs` to `src/dbus/manager/report_{MAJOR}_{NEW}/mod.rs`.

## Step 3: Update registration mod.rs files

### 3a. Blockdev — `src/dbus/blockdev/mod.rs`

1. Add module declaration: `mod blockdev_{MAJOR}_{NEW};` (after the last `blockdev_*` mod line)
2. Add re-export: `pub use blockdev_{MAJOR}_{NEW}::BlockdevR{NEW};` (after the last `BlockdevR*` pub use line)
3. In `register_blockdev`, add a new registration block after the last one, following the `if let Err(e)` pattern:
   ```rust
   if let Err(e) = BlockdevR{NEW}::register(
       engine.clone(),
       connection,
       manager,
       path.clone(),
       pool_uuid,
       dev_uuid,
   )
   .await
   {
       warn!("Failed to register interface blockdev.r{NEW} for pool with UUID {pool_uuid}: {e}");
   };
   ```
4. In `unregister_blockdev`, add: `BlockdevR{NEW}::unregister(connection, path.clone()).await?;` (after the last unregister line)

### 3b. Filesystem — `src/dbus/filesystem/mod.rs`

1. Add module declaration: `mod filesystem_{MAJOR}_{NEW};`
2. Add re-export: `pub use filesystem_{MAJOR}_{NEW}::FilesystemR{NEW};`
3. In `register_filesystem`, add a new registration block after the last one, using the `?` error propagation pattern (NOT `if let Err`):
   ```rust
   FilesystemR{NEW}::register(
       engine.clone(),
       connection,
       manager,
       path.clone(),
       pool_uuid,
       uuid,
   )
   .await?;
   ```
4. In `unregister_filesystem`, add: `FilesystemR{NEW}::unregister(connection, path.clone()).await?;`

### 3c. Pool — `src/dbus/pool/mod.rs`

1. Add module declaration: `mod pool_{MAJOR}_{NEW};`
2. Add re-export: `pub use pool_{MAJOR}_{NEW}::PoolR{NEW};`
3. In `register_pool`, add a new registration block after the last one, following the `if let Err(e)` pattern:
   ```rust
   if let Err(e) = PoolR{NEW}::register(
       engine,
       connection,
       manager,
       counter,
       path.clone(),
       pool_uuid,
   )
   .await
   {
       warn!("Failed to register interface pool.r{NEW} for pool with UUID {pool_uuid}: {e}");
   }
   ```
4. In `unregister_pool`, add a new unregister block after the last one:
   ```rust
   if let Err(e) = PoolR{NEW}::unregister(connection, path.clone()).await {
       warn!("Failed to deregister interface pool.r{NEW} for path {path}: {e}");
   }
   ```

### 3d. Manager — `src/dbus/manager/mod.rs`

1. Add module declarations: `mod manager_{MAJOR}_{NEW};` and `mod report_{MAJOR}_{NEW};`
2. Add re-exports: `pub use manager_{MAJOR}_{NEW}::ManagerR{NEW};` and `pub use report_{MAJOR}_{NEW}::ReportR{NEW};`
3. In `register_manager`, add manager registration after the last `ManagerR*` block:
   ```rust
   if let Err(e) = ManagerR{NEW}::register(engine, connection, manager, counter).await {
       warn!("Failed to register interface Manager.r{NEW}: {e}");
   }
   ```
4. In `register_manager`, add report registration after the last `ReportR*` block:
   ```rust
   if let Err(e) = ReportR{NEW}::register(engine, connection).await {
       warn!("Failed to register interface Report.r{NEW}: {e}");
   }
   ```

## Step 4: Update stratisd.conf

In `stratisd.conf`, add new allow rules at the end of each respective group (before the closing `</policy>` tag, maintaining the existing grouping order):

1. After the last `Report.r{CURRENT}` allow entry, add:
   ```xml
   <allow send_destination="org.storage.stratis3"
          send_interface="org.storage.stratis3.Report.r{NEW}"/>
   ```

2. After the last `Manager.r{CURRENT}` EngineStateReport entry, add:
   ```xml
   <allow send_destination="org.storage.stratis3"
          send_interface="org.storage.stratis3.Manager.r{NEW}"
          send_member="EngineStateReport"/>
   ```

3. After the last `Manager.r{CURRENT}` ListKeys entry, add:
   ```xml
   <allow send_destination="org.storage.stratis3"
          send_interface="org.storage.stratis3.Manager.r{NEW}"
          send_member="ListKeys"/>
   ```

## Step 5: Update _constants.py

In `tests/client-dbus/src/stratisd_client_dbus/_constants.py`, change:
```python
REVISION_NUMBER = {CURRENT}
```
to:
```python
REVISION_NUMBER = {NEW}
```

## Step 6: Build

Run `cargo build` in the stratisd project directory. Fix any compilation errors before proceeding.

## Step 7: Update introspection data

Do NOT run these commands yourself — they require sudo. Instead, after the build succeeds, give the user these instructions to run manually:

```bash
# 1. Start stratisd with the sim engine
sudo ./target/debug/stratisd --sim &

# 2. Wait a few seconds, then regenerate introspection data
sudo python /path/to/ci/misc_scripts/update_introspection_data.py python >| tests/client-dbus/src/stratisd_client_dbus/_introspect.py

# 3. Stop the background stratisd process
sudo kill $(pgrep -f 'stratisd --sim')

# 4. Verify the generated file references r{NEW} in interface names
grep 'r{NEW}' tests/client-dbus/src/stratisd_client_dbus/_introspect.py | head
```

## Important notes

- The new revision is always an exact copy of the previous revision with just the struct names and interface annotation strings updated. New methods/properties are added manually afterward.
- The `MAJOR` version (currently `3`) is baked into all D-Bus paths and interface names as `stratis3`.
- All prior revisions (r0 through the current) remain registered simultaneously for backward compatibility.
- The update_introspection_data.py script requires root because it talks to stratisd over the system D-Bus.
- If the build fails, check that all struct names and interface annotations were updated consistently and that all mod.rs registrations use the correct argument patterns for each type.
