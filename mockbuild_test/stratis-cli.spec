Name:           stratis-cli
Version:        V
Release:        D%{?dist}
Summary:        Command-line tool for interacting with the Stratis daemon

License:        Apache-2.0
URL:            https://github.com/stratis-storage/stratis-cli
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  %{_bindir}/a2x
%if 0%{?rhel}
BuildRequires:  python3-dateutil
BuildRequires:  python3-dbus-client-gen
BuildRequires:  python3-dbus-python-client-gen
BuildRequires:  python3-justbytes
BuildRequires:  python3-packaging
BuildRequires:  python3-psutil
BuildRequires:  python3-wcwidth
%endif

# Require the version of stratisd that supports a compatible D-Bus interface
Requires:       (stratisd >= VS with stratisd < 4.0.0)

# Exclude the same arches for stratis-cli as are excluded for stratisd
ExclusiveArch:  %{rust_arches} noarch
%if 0%{?rhel}
ExcludeArch:    i686
%endif
BuildArch:      noarch

%description
Stratis-cli test build.  This package should not be used in production

%prep
%autosetup

%build
%py3_build
a2x -f manpage docs/stratis.txt

%install
%py3_install
%{__install} -Dpm0644 -t %{buildroot}%{_mandir}/man8 docs/stratis.8

%files
%license LICENSE
%doc README.rst
%{_bindir}/stratis
%{_mandir}/man8/stratis.8*
%{python3_sitelib}/stratis_cli/
%{python3_sitelib}/stratis_cli-*.egg-info/

%changelog
* Fri Mar 22 2233 Stratis Team <stratis-team@redhat.com> - 77.77.77-77
- Update to 77.77.77-77
