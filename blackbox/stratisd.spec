%bcond_without check

%global udevdir %(pkg-config --variable=udevdir udev)
%global dracutdir %(pkg-config --variable=dracutdir dracut)

Name:           stratisd
Version:        3.5.0
Release:        77%{?dist}
Summary:        Daemon that manages block devices to create filesystems

# ASL 2.0
# ASL 2.0 or Boost
# ASL 2.0 or MIT
# BSD
# ISC
# MIT
# MIT or ASL 2.0
# MPLv2.0
# Unlicense or MIT
License:        MPLv2.0
URL:            https://github.com/stratis-storage/stratisd
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz
Source1:        %{url}/releases/download/v%{version}/%{name}-%{version}-vendor.tar.gz
Source2:        %{crates_source}


ExclusiveArch:  %{rust_arches}
%if 0%{?rhel} && !0%{?eln}
ExcludeArch:    i686
%endif

BuildRequires:  rust-srpm-macros
BuildRequires:  systemd-devel
BuildRequires:  dbus-devel
BuildRequires:  libblkid-devel
BuildRequires:  cryptsetup-devel
BuildRequires:  clang
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
Recommends:     clevis-luks >= 18

%description
%{summary}. This package should not be used in production.

%package dracut
Summary: Dracut modules for use with stratisd

ExclusiveArch:  %{rust_arches}

Requires:     stratisd
Requires:     dracut >= 051
Requires:     plymouth

%description dracut
%{summary}. This package should not be used in production.

%prep
%setup -q
tar --strip-components=1 --extract --verbose --file %{SOURCE2}
# Patches must be applied after the upstream package is extracted.
%cargo_prep -V 1

%build
%if 0%{?rhel} && !0%{?eln}
%{cargo_build} --bin=stratisd
%{cargo_build} --bin=stratis-min --bin=stratisd-min --bin=stratis-utils --no-default-features --features engine,min,systemd_compat
%else
%{__cargo} build %{?__cargo_common_opts} --release --bin=stratisd
%{__cargo} build %{?__cargo_common_opts} --release --bin=stratis-min --bin=stratisd-min --bin=stratis-utils --no-default-features --features engine,min,systemd_compat
%endif
a2x -f manpage docs/stratisd.txt

%install
%make_install DRACUTDIR=%{dracutdir} PROFILEDIR=release

%if %{with check}
%check
%cargo_test --no-run
%endif

%post
%systemd_post stratisd.service

%preun
%systemd_preun stratisd.service

%postun
%systemd_postun_with_restart stratisd.service

%files
%license LICENSE
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
%{_bindir}/stratis-min
%{_libexecdir}/stratisd-min
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

%changelog
* Fri Mar 22 2233 Stratis Team <stratis-team@redhat.com> - 77.77.77-77
- Update to 77.77.77-77
