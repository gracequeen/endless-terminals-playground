Need vm.swappiness dropped to 10 on this box — currently at the default 60. Make it persistent across reboots too, not just a runtime tweak. Config should live in /etc/sysctl.d/99-swap.conf.
