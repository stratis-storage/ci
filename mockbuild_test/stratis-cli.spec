Name:           stratis-cli
Version:        3.6.0
Release:        77%{?dist}
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
# It runs without, but totally useless
Requires:       (stratisd >= 3.6.0 with stratisd < 4.0.0)

# stratisd only available on certain arches
ExclusiveArch:  %{rust_arches} noarch
%if 0%{?rhel} && !0%{?eln}
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
# Do not install tab-completion files for RHEL
%if !0%{?rhel}
%{__install} -Dpm0644 -t %{buildroot}%{_datadir}/bash-completion/completions \
  shell-completion/bash/stratis
%{__install} -Dpm0644 -t %{buildroot}%{_datadir}/zsh/site-functions \
  shell-completion/zsh/_stratis
%{__install} -Dpm0644 -t %{buildroot}%{_datadir}/fish/vendor_completions.d \
  shell-completion/fish/stratis.fish
%endif
%{__install} -Dpm0644 -t %{buildroot}%{_mandir}/man8 docs/stratis.8

%files
%license LICENSE
%doc README.rst
%{_bindir}/stratis
%{_mandir}/man8/stratis.8*
%if !0%{?rhel}
%dir %{_datadir}/bash-completion
%dir %{_datadir}/bash-completion/completions
%{_datadir}/bash-completion/completions/stratis
%dir %{_datadir}/zsh
%dir %{_datadir}/zsh/site-functions
%{_datadir}/zsh/site-functions/_stratis
%dir %{_datadir}/fish
%dir %{_datadir}/fish/vendor_completions.d
%{_datadir}/fish/vendor_completions.d/stratis.fish
%endif
%{python3_sitelib}/stratis_cli/
%{python3_sitelib}/stratis_cli-*.egg-info/

%changelog
* Fri Mar 22 2233 Stratis Team <stratis-team@redhat.com> - 77.77.77-77
- Update to 77.77.77-77
