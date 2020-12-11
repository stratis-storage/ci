%bcond_without check

# Not interested in packaging lib
# stratisd is supposed to be daemon used through dbus
%global __cargo_is_lib() false
%global udevdir %(pkg-config --variable=udevdir udev)

Name:           stratisd
Version:        77.77.77
Release:        77%{?dist}
Summary:        Daemon that manages block devices to create filesystems

License:        MPLv2.0
URL:            https://github.com/stratis-storage/stratisd
%if 0%{?rhel}
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz
Source1:        %{name}-%{version}-vendor.tar.xz
%else
Source:         %{url}/archive/v%{version}/%{name}-%{version}.tar.gz
%endif

ExclusiveArch:  %{rust_arches}

%if 0%{?rhel}
BuildRequires:  rust-toolset
%else
BuildRequires:  rust-packaging
%endif

BuildRequires:  systemd-devel
BuildRequires:  dbus-devel
BuildRequires:  libblkid-devel
BuildRequires:  cryptsetup-devel
BuildRequires:  clang
BuildRequires:  %{_bindir}/a2x

Requires:       xfsprogs
Requires:       device-mapper-persistent-data
Requires:       systemd-libs
Requires:       dbus-libs
Requires:       clevis-luks >= 15

%description
Stratisd test build.  This package should not be used in production


%prep
%if 0%{?rhel}
%setup -q -n %{name}-%{version}

# Source1 is vendored dependencies
%cargo_prep -V 1
%else
%autosetup -p1
%cargo_prep
%generate_buildrequires
%cargo_generate_buildrequires
echo '/usr/bin/a2x'
%endif

%build
%cargo_build
a2x -f manpage docs/stratisd.txt

%install
%cargo_install
%{__install} -Dpm0644 -t %{buildroot}%{_datadir}/dbus-1/system.d stratisd.conf
# Daemon should be really private
mkdir -p %{buildroot}%{_libexecdir}
mkdir -p %{buildroot}%{udevdir}
mkdir -p %{buildroot}/developer_tools
mv %{buildroot}%{_bindir}/stratisd %{buildroot}%{_libexecdir}/stratisd
mv %{buildroot}%{_bindir}/stratis_uuids_to_names %{buildroot}%{udevdir}/stratis_uuids_to_names
%{__install} -Dpm0644 -t %{buildroot}%{_mandir}/man8 docs/stratisd.8
%{__install} -Dpm0644 -t %{buildroot}%{_udevrulesdir} udev/11-stratisd.rules
%{__install} -Dpm0644 -t %{buildroot}%{_unitdir} stratisd.service
%{__install} -Dpm0755 -t %{buildroot}%{_bindir} developer_tools/stratis_migrate_symlinks.sh

%if %{with check}
%check
%cargo_test -- -- --skip real_ --skip loop_ --skip travis_
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
%{udevdir}/stratis_uuids_to_names
%{_bindir}/stratis_dbusquery_version
%{_bindir}/stratis_migrate_symlinks.sh
%dir %{_datadir}/dbus-1
%{_datadir}/dbus-1/system.d/stratisd.conf
%{_mandir}/man8/stratisd.8*
%{_unitdir}/stratisd.service
%config %{_udevrulesdir}/11-stratisd.rules

%changelog
* Fri Mar 22 2233 Stratis Team <stratis-team@redhat.com> - 77.77.77-77
- Update to 77.77.77-77
