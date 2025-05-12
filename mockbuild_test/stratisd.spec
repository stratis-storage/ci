%bcond_without check

%global udevdir %(pkg-config --variable=udevdir udev)
%global dracutdir %(pkg-config --variable=dracutdir dracut)

Name:           stratisd
Version:        V
Release:        D%{?dist}
Summary:        Daemon that manages block devices to create filesystems

License:        MPL-2.0
URL:            https://github.com/stratis-storage/stratisd
Source0:        %{url}/archive/stratisd-v%{version}/%{name}-%{version}.tar.gz
Source1:        %{url}/releases/download/stratisd-v%{version}/%{name}-%{version}-vendor.tar.gz


ExclusiveArch:  %{rust_arches}
%if 0%{?rhel}
ExcludeArch:    i686
%endif

%if 0%{?rhel}
BuildRequires:  rust-toolset
%else
BuildRequires:  rust-packaging
%endif
BuildRequires:  rust-srpm-macros
BuildRequires:  systemd-devel
BuildRequires:  dbus-devel
BuildRequires:  libblkid-devel
BuildRequires:  cryptsetup-devel
BuildRequires:  clang
BuildRequires:  glibc-static
BuildRequires:  device-mapper-devel
BuildRequires:  %{_bindir}/a2x

# Required to calculate install directories
BuildRequires:  systemd
BuildRequires:  dracut

Requires:       xfsprogs
Requires:       device-mapper-persistent-data
Requires:       systemd-libs
Requires:       dbus-libs
Requires:       cryptsetup-libs
Requires:       libblkid

# stratisd does not require clevis; it can be used in restricted environments
# where clevis is not available.
# If using encryption via clevis, stratisd requires the instance of clevis
# that it uses to have been built in an environment with cryptsetup >= 2.6.0.
Recommends:     clevis-luks >= 18

%description
%{summary}. This package should not be used in production.

%package dracut
Summary: Dracut modules for use with stratisd

ExclusiveArch:  %{rust_arches}
%if 0%{?rhel}
ExcludeArch:    i686
%endif

Requires:     stratisd
Requires:     dracut >= 051
Requires:     systemd

%description dracut
%{summary}. This package should not be used in production.

%package tools
Summary: Tools that support Stratis operation

ExclusiveArch:  %{rust_arches}
%if 0%{?rhel}
ExcludeArch:    i686
%endif

Requires:     stratisd

%description tools
%{summary}. This package should not be used in production.

%prep
%autosetup -n stratisd-stratisd-v%{version} %{?rhel:-a1}

%if 0%{?rhel}
%cargo_prep -v vendor
%else
%cargo_prep
%generate_buildrequires
%cargo_generate_buildrequires -f engine,dbus_enabled,min,systemd_compat,extras,udev_scripts
%endif

%build
%{cargo_license -f engine,dbus_enabled,min,systemd_compat,extras,udev_scripts} > LICENSE.dependencies
%{__cargo} build %{?__cargo_common_opts} --release --bin=stratisd
%{__cargo} build %{?__cargo_common_opts} --release --bin=stratis-min --bin=stratisd-min --bin=stratis-utils --no-default-features --features engine,min,systemd_compat
%{__cargo} rustc %{?__cargo_common_opts} --release --bin=stratis-str-cmp --no-default-features --features udev_scripts -- -Ctarget-feature=+crt-static
%{__cargo} rustc %{?__cargo_common_opts} --release --bin=stratis-base32-decode --no-default-features --features udev_scripts -- -Ctarget-feature=+crt-static
%{__cargo} build %{?__cargo_common_opts} --release --bin=stratisd-tools --no-default-features --features engine,extras
a2x -f manpage docs/stratisd.txt
a2x -f manpage docs/stratis-dumpmetadata.txt
%{cargo_vendor_manifest}

%install
%make_install DRACUTDIR=%{dracutdir} PROFILEDIR=release

%if %{with check}
%check
%if 0%{?rhel} && 0%{?rhel} < 10
%cargo_test --no-run
%else
%cargo_test -- --no-run
%endif
%endif

%post
%systemd_post stratisd.service

%preun
%systemd_preun stratisd.service

%postun
%systemd_postun_with_restart stratisd.service

%files
%license LICENSE
%license LICENSE.dependencies
%license cargo-vendor.txt
%doc README.md
%{_libexecdir}/stratisd
%dir %{_datadir}/dbus-1
%dir %{_datadir}/dbus-1/system.d
%{_datadir}/dbus-1/system.d/stratisd.conf
%{_mandir}/man8/stratisd.8*
%{_unitdir}/stratisd.service
%{_udevrulesdir}/61-stratisd.rules
%{udevdir}/stratis-str-cmp
%{udevdir}/stratis-base32-decode
%{_bindir}/stratis-predict-usage
%{_unitdir}/stratisd-min-postinitrd.service
%{_unitdir}/stratis-fstab-setup@.service
%{_unitdir}/stratis-fstab-setup-with-network@.service
%{_bindir}/stratis-min
%{_libexecdir}/stratisd-min
%{_bindir}/stratis-decode-dm
%{_systemd_util_dir}/stratis-fstab-setup


%files dracut
%license LICENSE
%{dracutdir}/modules.d/90stratis-clevis/module-setup.sh
%{dracutdir}/modules.d/90stratis-clevis/stratis-clevis-rootfs-setup
%{dracutdir}/modules.d/90stratis/61-stratisd.rules
%{dracutdir}/modules.d/90stratis/module-setup.sh
%{dracutdir}/modules.d/90stratis/stratis-rootfs-setup
%{dracutdir}/modules.d/90stratis/stratisd-min.service
%{_systemd_util_dir}/system-generators/stratis-clevis-setup-generator
%{_systemd_util_dir}/system-generators/stratis-setup-generator

%files tools
%license LICENSE
%{_bindir}/stratisd-tools
%{_bindir}/stratis-dumpmetadata
%{_mandir}/man8/stratis-dumpmetadata.8*

%changelog
* Fri Mar 22 2233 Stratis Team <stratis-team@redhat.com> - 77.77.77-77
- Update to 77.77.77-77
