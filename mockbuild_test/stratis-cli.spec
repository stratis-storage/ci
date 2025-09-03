Name:           stratis-cli
Version:        V
Release:        D%{?dist}
Summary:        Command-line tool for interacting with the Stratis daemon

License:        Apache-2.0
URL:            https://github.com/stratis-storage/stratis-cli
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildRequires:  python3-devel
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

%generate_buildrequires
%pyproject_buildrequires

%build
%pyproject_wheel
a2x -f manpage docs/stratis.txt

%install
%pyproject_install
%pyproject_save_files -l stratis_cli
%{__install} -Dpm0644 -t %{buildroot}%{_mandir}/man8 docs/stratis.8

%check
%pyproject_check_import

%files -f %{pyproject_files}
%doc README.rst
%{_bindir}/stratis
%{_mandir}/man8/stratis.8*

%changelog
* Fri Mar 22 2233 Stratis Team <stratis-team@redhat.com> - 77.77.77-77
- Update to 77.77.77-77
