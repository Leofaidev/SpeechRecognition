# Allow outbound SSH to VM regardless of VPN kill switch
New-NetFirewallRule -DisplayName "Allow SSH to VMware VM" `
    -Direction Outbound -Action Allow -Protocol TCP `
    -RemoteAddress "192.168.153.129" -RemotePort 22 `
    -InterfaceAlias "VMware Network Adapter VMnet8" `
    -ErrorAction SilentlyContinue

# Also allow inbound reply traffic
New-NetFirewallRule -DisplayName "Allow SSH reply from VMware VM" `
    -Direction Inbound -Action Allow -Protocol TCP `
    -RemoteAddress "192.168.153.129" -RemotePort 22 `
    -InterfaceAlias "VMware Network Adapter VMnet8" `
    -ErrorAction SilentlyContinue

"Done" | Out-File C:\Users\Leo1\route_result.txt
Get-NetFirewallRule -DisplayName "Allow SSH to VMware VM" | Select-Object DisplayName, Enabled, Direction, Action | Out-File -Append C:\Users\Leo1\route_result.txt
