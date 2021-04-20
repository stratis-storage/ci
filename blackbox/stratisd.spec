%bcond_without check

# Not interested in packaging lib
# stratisd is supposed to be daemon used through dbus
%global __cargo_is_lib() false
%global udevdir %(pkg-config --variable=udevdir udev)
%global dracutdir %(pkg-config --variable=dracutdir dracut)

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

Recommends:     dracut >= 051
Recommends:     clevis-luks >= 15

%description
Stratisd test build.  This package should not be used in production


%prep
%setup -q -n %{name}-%{version}

# Source1 is vendored dependencies
%cargo_prep -V 1

%build
%cargo_build
%cargo_build --bin=stratis-min --bin=stratisd-min --bin=stratis-utils --no-default-features --features min,systemd_compat
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
%{__install} -Dpm0644 -t %{buildroot}%{_unitdir} systemd/stratisd.service
%{__install} -Dpm0644 -t %{buildroot}%{dracutdir}/dracut.conf.d dracut/90-stratis.conf
mkdir -p %{buildroot}%{dracutdir}/modules.d/90stratis
%{__install} -Dpm0755 -t %{buildroot}%{dracutdir}/modules.d/90stratis dracut/90stratis/module-setup.sh
%{__install} -Dpm0755 -t %{buildroot}%{dracutdir}/modules.d/90stratis dracut/90stratis/stratis-rootfs-setup
%{__install} -Dpm0644 -t %{buildroot}%{dracutdir}/modules.d/90stratis dracut/90stratis/stratisd-min.service
%{__install} -Dpm0644 -t %{buildroot}%{dracutdir}/modules.d/90stratis dracut/90stratis/61-stratisd.rules
mkdir -p %{buildroot}%{dracutdir}/modules.d/90stratis-clevis
%{__install} -Dpm0755 -t %{buildroot}%{dracutdir}/modules.d/90stratis-clevis dracut/90stratis-clevis/module-setup.sh
%{__install} -Dpm0755 -t %{buildroot}%{dracutdir}/modules.d/90stratis-clevis dracut/90stratis-clevis/stratis-clevis-rootfs-setup
%{__install} -Dpm0644 -t %{buildroot}%{_unitdir} systemd/stratisd-min-postinitrd.service

mkdir -p %{buildroot}%{udevdir}
mv %{buildroot}%{_bindir}/stratis-utils %{buildroot}%{udevdir}/stratis_utils
mv %{buildroot}%{udevdir}/stratis_utils %{buildroot}%{udevdir}/stratis-str-cmp
ln %{buildroot}%{udevdir}/stratis-str-cmp %{buildroot}%{udevdir}/stratis-base32-decode
ln %{buildroot}%{udevdir}/stratis-str-cmp %{buildroot}%{_bindir}/stratis-predict-usage
mkdir -p %{buildroot}%{_unitdir}/system-generators
ln %{buildroot}%{udevdir}/stratis-str-cmp %{buildroot}%{_unitdir}/system-generators/stratis-clevis-setup-generator
ln %{buildroot}%{udevdir}/stratis-str-cmp %{buildroot}%{_unitdir}/system-generators/stratis-setup-generator
%{__install} -Dpm0755 -t %{buildroot}%{_bindir} target/release/stratis-min
%{__install} -Dpm0755 -t %{buildroot}%{_libexecdir} target/release/stratisd-min

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
%{_bindir}/stratis-predict-usage
%{dracutdir}/dracut.conf.d/90-stratis.conf
%{dracutdir}/modules.d/90stratis-clevis/module-setup.sh
%{dracutdir}/modules.d/90stratis-clevis/stratis-clevis-rootfs-setup
%{dracutdir}/modules.d/90stratis/61-stratisd.rules
%{dracutdir}/modules.d/90stratis/module-setup.sh
%{dracutdir}/modules.d/90stratis/stratis-rootfs-setup
%{dracutdir}/modules.d/90stratis/stratisd-min.service
%{_unitdir}/stratisd-min-postinitrd.service
%{_unitdir}/system-generators/stratis-clevis-setup-generator
%{_unitdir}/system-generators/stratis-setup-generator
%{_bindir}/stratis-min
%{_libexecdir}/stratisd-min



%changelog
* Fri Mar 22 2233 Stratis Team <stratis-team@redhat.com> - 77.77.77-77
- Update to 77.77.77-77
