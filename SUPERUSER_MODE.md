# Superuser Mode Documentation

## ⚠️ SECURITY WARNING

**Superuser mode is a POWERFUL and DANGEROUS feature that allows the AI agent to execute commands with sudo/root privileges.**

**Only enable this feature in:**
- ✅ Isolated development environments
- ✅ Dedicated test/staging systems
- ✅ Containerized/sandboxed environments
- ✅ Systems where you have full control and regular backups

**NEVER enable this feature in:**
- ❌ Production systems
- ❌ Shared environments
- ❌ Systems with sensitive data
- ❌ Public-facing servers
- ❌ Systems without proper backups

---

## Overview

Superuser mode extends the terminal tool capabilities to allow execution of commands that require elevated privileges (sudo). This is useful for:

- Installing system packages (apt, yum, dnf, pacman)
- Managing system services (systemctl, service)
- Changing file permissions and ownership (chmod, chown)
- Managing users and groups
- Docker operations that require root

## Configuration

### Enable Superuser Mode

Add to your `.env` file:

```bash
# Enable sudo commands (default: false)
SUPERUSER_MODE=true

# Require confirmation before sudo execution (default: true)
REQUIRE_SUDO_CONFIRMATION=true
```

### Settings Explained

| Setting | Default | Description |
|---------|---------|-------------|
| `SUPERUSER_MODE` | `false` | Master switch for sudo commands. Must be `true` to allow any sudo operations. |
| `REQUIRE_SUDO_CONFIRMATION` | `true` | If enabled, system will ask for confirmation before executing sudo commands. |

## Allowed Sudo Commands

When superuser mode is enabled, the following commands can be executed with sudo:

### Package Managers
- `apt`, `apt-get` (Debian/Ubuntu)
- `yum`, `dnf` (RedHat/CentOS/Fedora)
- `pacman` (Arch Linux)

### Service Management
- `systemctl` (systemd)
- `service` (SysV init)

### Permission Management
- `chmod` (change file permissions)
- `chown` (change file ownership)
- `chgrp` (change group ownership)

### User Management
- `useradd` (add user)
- `userdel` (delete user)
- `usermod` (modify user)

### Container Management
- `docker`
- `docker-compose`

## Always Blocked Commands

The following commands are **NEVER** allowed, even with sudo and superuser mode enabled:

- ❌ `rm`, `rmdir`, `del` - File deletion (use delete_file tool instead)
- ❌ `format`, `mkfs`, `dd` - Disk formatting operations
- ❌ `shutdown`, `reboot`, `poweroff`, `halt` - System power control
- ❌ `kill`, `killall`, `pkill` - Process termination
- ❌ `iptables`, `ufw`, `firewall-cmd` - Firewall modifications
- ❌ `mount`, `umount` - Filesystem mounting

These commands are blocked to prevent accidental system damage, even with explicit sudo.

## Usage Examples

### With Superuser Mode Enabled

```python
# Install a system package
terminal.execute(command="sudo apt update")
terminal.execute(command="sudo apt install nginx -y")

# Manage services
terminal.execute(command="sudo systemctl start nginx")
terminal.execute(command="sudo systemctl status nginx")
terminal.execute(command="sudo systemctl enable nginx")

# Change file permissions
terminal.execute(command="sudo chmod 755 /var/www/html/script.sh")
terminal.execute(command="sudo chown www-data:www-data /var/www/html/index.html")

# Docker operations
terminal.execute(command="sudo docker ps")
terminal.execute(command="sudo docker-compose up -d")

# User management
terminal.execute(command="sudo useradd -m newuser")
terminal.execute(command="sudo usermod -aG sudo newuser")
```

### With Superuser Mode Disabled (Default)

Attempting sudo commands will result in an error with helpful guidance:

```
❌ Command blocked for safety: Sudo commands are disabled

💡 Suggestion: Superuser mode is currently DISABLED. To enable sudo commands:
1. Set SUPERUSER_MODE=true in your .env file
2. Restart the application
WARNING: Only enable this in trusted environments!
```

## How It Works

### Command Validation Flow

1. **Parse Command**: Extract base command and check for `sudo` prefix
2. **Check Superuser Mode**: If sudo detected and mode disabled → BLOCK
3. **Check Blacklist**: Commands like `rm`, `dd`, `shutdown` → ALWAYS BLOCK
4. **Check Dangerous Patterns**: Fork bombs, disk wiping → ALWAYS BLOCK
5. **Validate Against Whitelist**: Ensure command is in allowed list
6. **Log Warning**: Log all sudo command attempts for audit trail
7. **Execute**: If all checks pass, execute with sudo privileges

### Safety Layers

#### Layer 1: Configuration
- Superuser mode must be explicitly enabled in settings
- Default is always `false` (disabled)

#### Layer 2: Command Whitelist
- Only pre-approved commands can use sudo
- Unknown commands are rejected with helpful message

#### Layer 3: Pattern Detection
- Dangerous patterns (e.g., `rm -rf /`, fork bombs) are always blocked
- Pattern matching is case-insensitive

#### Layer 4: Logging & Audit
- All sudo command attempts are logged with WARNING level
- Format: `⚠️  SUDO command requested: <command>`
- Helps track what operations were performed

#### Layer 5: Confirmation (Optional)
- If `REQUIRE_SUDO_CONFIRMATION=true`, user must confirm
- Provides one last chance to review before execution

## Error Messages

The tool provides context-aware error messages to guide users:

### Sudo Disabled
```
❌ Command blocked for safety: Sudo commands are disabled. Enable SUPERUSER_MODE
in settings to use sudo. WARNING: This should only be enabled in trusted environments!

💡 Suggestion: Superuser mode is currently DISABLED. To enable sudo commands:
1. Set SUPERUSER_MODE=true in your .env file
2. Restart the application
WARNING: Only enable this in trusted environments!
```

### Command Not Allowed With Sudo
```
❌ Command blocked for safety: 'xyz' is not allowed with sudo. Allowed sudo commands:
apt, apt-get, chmod, chown, chgrp, docker, docker-compose, pacman, service, systemctl,
useradd, userdel, usermod, yum, dnf
```

### Dangerous Command
```
❌ Command blocked for safety: 'rm' is a dangerous command and is NEVER allowed,
even with sudo

💡 Suggestion: Use the 'delete_file' tool instead to safely delete files or directories.
```

## LLM Integration

The terminal tool description automatically updates based on superuser mode status:

### When Disabled
```
SUPERUSER MODE: ✗ DISABLED
Commands are validated for safety. Sudo commands require SUPERUSER_MODE=true in settings.
```

### When Enabled
```
SUPERUSER MODE: ✓ ENABLED
When enabled, you can run commands with sudo for:
• System package installation: sudo apt install package_name
• Service management: sudo systemctl start/stop service
• Permission changes: sudo chmod/chown files
• User management: sudo useradd/usermod username
• Docker operations: sudo docker commands
```

LLMs will see different examples based on mode:

**Disabled**: Only shows regular commands
**Enabled**: Includes sudo examples in the examples list

## Best Practices

### 1. Use Minimal Privileges
- Only enable superuser mode when absolutely necessary
- Disable it immediately after completing privileged tasks

### 2. Audit Logs
- Regularly review logs for sudo command executions
- Look for `⚠️  SUDO command requested:` entries
- Investigate any unexpected sudo usage

### 3. Containerization
- Run the agent in Docker container with limited capabilities
- Use volume mounts to restrict filesystem access
- Configure resource limits (CPU, memory, network)

### 4. Backup Before Use
- Always have recent backups before enabling superuser mode
- Test in isolated environment first
- Have rollback plan ready

### 5. Limit Scope
- Use `SANDBOX_MODE=true` to restrict file operations to workspace
- Configure `BLOCKED_PATHS` to protect critical directories
- Set appropriate `COMMAND_TIMEOUT_SECONDS` to prevent long-running commands

### 6. Monitor Resource Usage
- Watch for unexpected CPU/memory spikes
- Monitor network traffic
- Track disk usage changes

## Troubleshooting

### "Sudo requires a password" Error

If you get password prompts, configure passwordless sudo for the user:

```bash
# Edit sudoers file (as root)
sudo visudo

# Add line (replace 'username' with actual username)
username ALL=(ALL) NOPASSWD:ALL
```

**Note**: This removes password requirement - only do in isolated environments!

### "Permission denied" Even With Sudo

1. Check if user is in sudo/wheel group:
   ```bash
   groups username
   ```

2. Add user to sudo group if needed:
   ```bash
   sudo usermod -aG sudo username
   ```

### Commands Still Blocked

1. Verify `SUPERUSER_MODE=true` in `.env`
2. Restart the application after changing settings
3. Check if command is in `SUDO_WHITELIST`
4. Review logs for specific error message

## Security Checklist

Before enabling superuser mode, ensure:

- [ ] Running in isolated/dedicated environment
- [ ] Have recent, tested backups
- [ ] Reviewed and understand all allowed sudo commands
- [ ] Configured appropriate blocked paths
- [ ] Enabled audit logging
- [ ] Limited network access if possible
- [ ] Set up monitoring/alerting
- [ ] Documented why superuser mode is needed
- [ ] Have rollback plan ready
- [ ] Team/stakeholders are aware and approved

## Comparison: Superuser Mode vs Regular Mode

| Feature | Regular Mode | Superuser Mode |
|---------|-------------|----------------|
| Install system packages | ❌ No | ✅ Yes (sudo apt/yum/etc) |
| Install user packages | ✅ Yes (pip, npm) | ✅ Yes |
| Manage services | ❌ No | ✅ Yes (sudo systemctl) |
| Change permissions | ❌ No | ✅ Yes (sudo chmod/chown) |
| Docker operations | ⚠️ Limited | ✅ Yes (sudo docker) |
| File deletion | ❌ Use tool | ❌ Use tool (always) |
| System shutdown | ❌ Never | ❌ Never (always blocked) |
| User management | ❌ No | ✅ Yes (sudo useradd/etc) |

## Related Configuration

Superuser mode works alongside other security settings:

```bash
# Sandbox mode restricts file operations to working directory
SANDBOX_MODE=true

# Working directory - agent can only access files here
WORKING_DIRECTORY=/workspace

# Block access to critical paths
BLOCKED_PATHS=/etc,/sys,/proc,/root,/boot

# Limit command execution time
COMMAND_TIMEOUT_SECONDS=300

# Require confirmation for dangerous operations
REQUIRE_SUDO_CONFIRMATION=true
```

## Version History

- **v2.0.0**: Initial superuser mode implementation
  - Added `SUPERUSER_MODE` setting
  - Added `REQUIRE_SUDO_CONFIRMATION` setting
  - Implemented sudo command validation
  - Added `SUDO_WHITELIST` for allowed commands
  - Enhanced error messages with sudo suggestions
  - Added audit logging for sudo attempts

## Support

If you encounter issues with superuser mode:

1. Check logs in `logs/agent.log`
2. Review security warnings in console
3. Verify `.env` configuration
4. Test with `superuser_mode: false` first
5. Consult this documentation for troubleshooting

---

**Remember**: With great power comes great responsibility. Use superuser mode wisely and only when absolutely necessary!
