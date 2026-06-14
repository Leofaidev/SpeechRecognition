#!/bin/bash
# Generate host keys
echo '1' | sudo -S mkdir -p /etc/dropbear
echo '1' | sudo -S dropbearkey -t rsa -f /etc/dropbear/dropbear_rsa_host_key 2>&1
echo '1' | sudo -S dropbearkey -t ed25519 -f /etc/dropbear/dropbear_ed25519_host_key 2>&1
# Start dropbear on port 2222 (background, no foreground flag)
echo '1' | sudo -S dropbear -p 2222 2>&1
sleep 2
ss -tlnp | grep 2222
echo DONE
