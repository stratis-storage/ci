
Name:           stratis-cli
Version:        3.1.0
Release:        77%{?dist}
Summary:        Command-line tool for interacting with the Stratis daemon

License:        ASL 2.0
URL:            https://github.com/stratis-storage/stratis-cli
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  %{_bindir}/a2x
# It runs without, but totally useless
#Requires:       (stratisd >= 1.0 with stratisd < 1.1)

# stratisd only available on certain arches
ExclusiveArch:  %{rust_arches} noarch
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
%{__install} -Dpm0644 -t %{buildroot}%{_datadir}/bash-completion/completions \
  shell-completion/bash/stratis
%{__install} -Dpm0644 -t %{buildroot}%{_datadir}/zsh/site-functions \
  shell-completion/zsh/_stratis
%{__install} -Dpm0644 -t %{buildroot}%{_mandir}/man8 docs/stratis.8

%files
%license LICENSE
%doc README.rst
%{_bindir}/stratis
%{_mandir}/man8/stratis.8*
%dir %{_datadir}/bash-completion
%dir %{_datadir}/bash-completion/completions
%{_datadir}/bash-completion/completions/stratis
%dir %{_datadir}/zsh
%dir %{_datadir}/zsh/site-functions
%{_datadir}/zsh/site-functions/_stratis
%{python3_sitelib}/stratis_cli/
%{python3_sitelib}/stratis_cli-*.egg-info/

%changelog
* Fri Mar 22 2233 Stratis Team <stratis-team@redhat.com> - 77.77.77-77
- Update to 77.77.77-77
