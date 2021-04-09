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
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz
Source1:        %{name}-%{version}-vendor.tar.xz


ExclusiveArch:  %{rust_arches}

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

Recommends:     clevis-luks >= 15

%description
Stratisd test build.  This package should not be used in production


%prep
%setup -q -n %{name}-%{version}

# Source1 is vendored dependencies
%cargo_prep -V 1

%build
%cargo_build
a2x -f manpage docs/stratisd.txt

%install
%cargo_install
%{__install} -Dpm0644 -t %{buildroot}%{_datadir}/dbus-1/system.d stratisd.conf
# Daemon should be really private
mkdir -p %{buildroot}%{_libexecdir}
mkdir -p %{buildroot}/developer_tools
mv %{buildroot}%{_bindir}/stratisd %{buildroot}%{_libexecdir}/stratisd
%{__install} -Dpm0644 -t %{buildroot}%{_mandir}/man8 docs/stratisd.8
%{__install} -Dpm0644 -t %{buildroot}%{_udevrulesdir} udev/61-stratisd.rules
%{__install} -Dpm0644 -t %{buildroot}%{_unitdir} stratisd.service

mkdir -p %{buildroot}%{udevdir}
mv %{buildroot}%{_bindir}/stratis-utils %{buildroot}%{udevdir}/stratis_utils
mv %{buildroot}%{udevdir}/stratis_utils %{buildroot}%{udevdir}/stratis-str-cmp
ln %{buildroot}%{udevdir}/stratis-str-cmp %{buildroot}%{udevdir}/stratis-base32-decode

%if %{with check}
%check
%cargo_test -- --skip real_ --skip loop_ --skip travis_
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
%{_datadir}/dbus-1/system.d/stratisd.conf
%{_mandir}/man8/stratisd.8*
%{_unitdir}/stratisd.service
%config %{_udevrulesdir}/61-stratisd.rules
%{udevdir}/stratis-str-cmp
%{udevdir}/stratis-base32-decode

%changelog
* Fri Mar 22 2233 Stratis Team <stratis-team@redhat.com> - 77.77.77-77
- Update to 77.77.77-77
