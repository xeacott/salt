# -*- coding: utf-8 -*-
"""
Module for managing Windows systems and getting Windows system information.
Support for reboot, shutdown, join domain, rename

:depends:
    - pywintypes
    - win32api
    - win32con
    - win32net
    - wmi
"""
from __future__ import absolute_import, print_function, unicode_literals

# Import Python libs
import ctypes
import logging
import platform
import time
from datetime import datetime

# Import salt libs
import salt.utils.functools
import salt.utils.locales
import salt.utils.platform
import salt.utils.win_system
import salt.utils.winapi
from salt.exceptions import CommandExecutionError
from salt.ext import six

try:
    import pywintypes
    import win32api
    import win32con
    import win32net
    import wmi
    from ctypes import windll

    HAS_WIN32NET_MODS = True
except ImportError:
    HAS_WIN32NET_MODS = False

# Set up logging
log = logging.getLogger(__name__)

# Define the module's virtual name
__virtualname__ = "system"


def __virtual__():
    """
    Only works on Windows Systems with Win32 Modules
    """
    if not salt.utils.platform.is_windows():
        return False, "Module win_system: Requires Windows"

    if not HAS_WIN32NET_MODS:
        return False, "Module win_system: Missing win32 modules"

    return __virtualname__


def halt(timeout=5, in_seconds=False):
    """
    Halt a running system.

    Args:

        timeout (int):
            Number of seconds before halting the system. Default is 5 seconds.

        in_seconds (bool):
            Whether to treat timeout as seconds or minutes.

            .. versionadded:: 2015.8.0

    Returns:
        bool: ``True`` if successful, otherwise ``False``

    CLI Example:

    .. code-block:: bash

        salt '*' system.halt 5 True
    """
    return salt.utils.win_system.halt(timeout=timeout, in_seconds=in_seconds)


def init(runlevel):  # pylint: disable=unused-argument
    """
    Change the system runlevel on sysV compatible systems. Not applicable to
    Windows

    CLI Example:

    .. code-block:: bash

        salt '*' system.init 3
    """
    return salt.utils.win_system.init(runlevel)


def poweroff(timeout=5, in_seconds=False):
    """
    Power off a running system.

    Args:

        timeout (int):
            Number of seconds before powering off the system. Default is 5
            seconds.

        in_seconds (bool):
            Whether to treat timeout as seconds or minutes.

            .. versionadded:: 2015.8.0

    Returns:
        bool: ``True`` if successful, otherwise ``False``

    CLI Example:

    .. code-block:: bash

        salt '*' system.poweroff 5
    """
    return salt.utils.win_system.shutdown(timeout=timeout, in_seconds=in_seconds)


def reboot(
    timeout=5,
    in_seconds=False,
    wait_for_reboot=False,  # pylint: disable=redefined-outer-name
    only_on_pending_reboot=False,
):
    """
    Reboot a running system.

    Args:

        timeout (int):
            The number of minutes/seconds before rebooting the system. Use of
            minutes or seconds depends on the value of ``in_seconds``. Default
            is 5 minutes.

        in_seconds (bool):
            ``True`` will cause the ``timeout`` parameter to be in seconds.
             ``False`` will be in minutes. Default is ``False``.

            .. versionadded:: 2015.8.0

        wait_for_reboot (bool)
            ``True`` will sleep for timeout + 30 seconds after reboot has been
            initiated. This is useful for use in a highstate. For example, you
            may have states that you want to apply only after the reboot.
            Default is ``False``.

            .. versionadded:: 2015.8.0

        only_on_pending_reboot (bool):
            If this is set to ``True``, then the reboot will only proceed
            if the system reports a pending reboot. Setting this parameter to
            ``True`` could be useful when calling this function from a final
            housekeeping state intended to be executed at the end of a state run
            (using *order: last*). Default is ``False``.

    Returns:
        bool: ``True`` if successful (a reboot will occur), otherwise ``False``

    CLI Example:

    .. code-block:: bash

        salt '*' system.reboot 5
        salt '*' system.reboot 5 True

    Invoking this function from a final housekeeping state:

    .. code-block:: yaml

        final_housekeeping:
           module.run:
              - name: system.reboot
              - only_on_pending_reboot: True
              - order: last
    """
    return salt.utils.win_system.reboot(timeout, in_seconds, wait_for_reboot, only_on_pending_reboot)


def shutdown(
    message=None,
    timeout=5,
    force_close=True,
    reboot=False,  # pylint: disable=redefined-outer-name
    in_seconds=False,
    only_on_pending_reboot=False,
):
    """
    Shutdown a running system.

    Args:

        message (str):
            The message to display to the user before shutting down.

        timeout (int):
            The length of time (in seconds) that the shutdown dialog box should
            be displayed. While this dialog box is displayed, the shutdown can
            be aborted using the ``system.shutdown_abort`` function.

            If timeout is not zero, InitiateSystemShutdown displays a dialog box
            on the specified computer. The dialog box displays the name of the
            user who called the function, the message specified by the lpMessage
            parameter, and prompts the user to log off. The dialog box beeps
            when it is created and remains on top of other windows (system
            modal). The dialog box can be moved but not closed. A timer counts
            down the remaining time before the shutdown occurs.

            If timeout is zero, the computer shuts down immediately without
            displaying the dialog box and cannot be stopped by
            ``system.shutdown_abort``.

            Default is 5 minutes

        in_seconds (bool):
            ``True`` will cause the ``timeout`` parameter to be in seconds.
             ``False`` will be in minutes. Default is ``False``.

            .. versionadded:: 2015.8.0

        force_close (bool):
            ``True`` will force close all open applications. ``False`` will
            display a dialog box instructing the user to close open
            applications. Default is ``True``.

        reboot (bool):
            ``True`` restarts the computer immediately after shutdown. ``False``
            powers down the system. Default is ``False``.

        only_on_pending_reboot (bool): If this is set to True, then the shutdown
            will only proceed if the system reports a pending reboot. To
            optionally shutdown in a highstate, consider using the shutdown
            state instead of this module.

        only_on_pending_reboot (bool):
            If ``True`` the shutdown will only proceed if there is a reboot
            pending. ``False`` will shutdown the system. Default is ``False``.

    Returns:
        bool:
            ``True`` if successful (a shutdown or reboot will occur), otherwise
            ``False``

    CLI Example:

    .. code-block:: bash

        salt '*' system.shutdown "System will shutdown in 5 minutes"
    """
    return salt.utils.win_system.shutdown(message, timeout, force_close, reboot, in_seconds, only_on_pending_reboot)


def shutdown_hard():
    """
    Shutdown a running system with no timeout or warning.

    Returns:
        bool: ``True`` if successful, otherwise ``False``

    CLI Example:

    .. code-block:: bash

        salt '*' system.shutdown_hard
    """
    return salt.utils.win_system.shutdown_hard()


def shutdown_abort():
    """
    Abort a shutdown. Only available while the dialog box is being
    displayed to the user. Once the shutdown has initiated, it cannot be
    aborted.

    Returns:
        bool: ``True`` if successful, otherwise ``False``

    CLI Example:

    .. code-block:: bash

        salt 'minion-id' system.shutdown_abort
    """
    return salt.utils.win_system.shutdown_abort()


def lock():
    """
    Lock the workstation.

    Returns:
        bool: ``True`` if successful, otherwise ``False``

    CLI Example:

    .. code-block:: bash

        salt 'minion-id' system.lock
    """
    return salt.utils.win_system.lock()


def set_computer_name(name):
    """
    Set the Windows computer name

    Args:

        name (str):
            The new name to give the computer. Requires a reboot to take effect.

    Returns:
        dict:
            Returns a dictionary containing the old and new names if successful.
            ``False`` if not.

    CLI Example:

    .. code-block:: bash

        salt 'minion-id' system.set_computer_name 'DavesComputer'
    """
    return salt.utils.win_system.set_computer_name(name)


def get_pending_computer_name():
    """
    Get a pending computer name. If the computer name has been changed, and the
    change is pending a system reboot, this function will return the pending
    computer name. Otherwise, ``None`` will be returned. If there was an error
    retrieving the pending computer name, ``False`` will be returned, and an
    error message will be logged to the minion log.

    Returns:
        str:
            Returns the pending name if pending restart. Returns ``None`` if not
            pending restart.

    CLI Example:

    .. code-block:: bash

        salt 'minion-id' system.get_pending_computer_name
    """
    return salt.utils.win_system._get_pending_computer_name()


def get_computer_name():
    """
    Get the Windows computer name

    Returns:
        str: Returns the computer name if found. Otherwise returns ``False``.

    CLI Example:

    .. code-block:: bash

        salt 'minion-id' system.get_computer_name
    """
    return salt.utils.win_system._get_computer_name()


def set_computer_desc(desc=None):
    """
    Set the Windows computer description

    Args:

        desc (str):
            The computer description

    Returns:
        str: Description if successful, otherwise ``False``

    CLI Example:

    .. code-block:: bash

        salt 'minion-id' system.set_computer_desc 'This computer belongs to Dave!'
    """
    return salt.utils.win_system.set_computer_desc(desc)


def get_system_info():
    """
    Get system information.

    .. note::

        Not all system info is available across all versions of Windows. If it
        is not available on an older version, it will be skipped

    Returns:
        dict: Dictionary containing information about the system to include
        name, description, version, etc...

    CLI Example:

    .. code-block:: bash

        salt 'minion-id' system.get_system_info
    """
    return salt.utils.win_system.get_system_info()


def get_computer_desc():
    """
    Get the Windows computer description

    Returns:
        str: Returns the computer description if found. Otherwise returns
        ``False``.

    CLI Example:

    .. code-block:: bash

        salt 'minion-id' system.get_computer_desc
    """
    return salt.utils.win_system.get_computer_desc()


def get_hostname():
    """
    Get the hostname of the windows minion

    .. versionadded:: 2016.3.0

    Returns:
        str: Returns the hostname of the windows minion

    CLI Example:

    .. code-block:: bash

        salt 'minion-id' system.get_hostname
    """
    cmd = "hostname"
    ret = __salt__["cmd.run"](cmd=cmd)
    return ret


def set_hostname(hostname):
    """
    Set the hostname of the windows minion, requires a restart before this will
    be updated.

    .. versionadded:: 2016.3.0

    Args:
        hostname (str): The hostname to set

    Returns:
        bool: ``True`` if successful, otherwise ``False``

    CLI Example:

    .. code-block:: bash

        salt 'minion-id' system.set_hostname newhostname
    """
    with salt.utils.winapi.Com():
        conn = wmi.WMI()
        comp = conn.Win32_ComputerSystem()[0]
        return comp.Rename(Name=hostname)


def join_domain(
    domain,
    username=None,
    password=None,
    account_ou=None,
    account_exists=False,
    restart=False,
):
    """
    Join a computer to an Active Directory domain. Requires a reboot.

    Args:

        domain (str):
            The domain to which the computer should be joined, e.g.
            ``example.com``

        username (str):
            Username of an account which is authorized to join computers to the
            specified domain. Needs to be either fully qualified like
            ``user@domain.tld`` or simply ``user``

        password (str):
            Password of the specified user

        account_ou (str):
            The DN of the OU below which the account for this computer should be
            created when joining the domain, e.g.
            ``ou=computers,ou=departm_432,dc=my-company,dc=com``

        account_exists (bool):
            If set to ``True`` the computer will only join the domain if the
            account already exists. If set to ``False`` the computer account
            will be created if it does not exist, otherwise it will use the
            existing account. Default is ``False``

        restart (bool):
            ``True`` will restart the computer after a successful join. Default
            is ``False``

            .. versionadded:: 2015.8.2/2015.5.7

    Returns:
        dict: Returns a dictionary if successful, otherwise ``False``

    CLI Example:

    .. code-block:: bash

        salt 'minion-id' system.join_domain domain='domain.tld' \\
                         username='joinuser' password='joinpassword' \\
                         account_ou='ou=clients,ou=org,dc=domain,dc=tld' \\
                         account_exists=False, restart=True
    """
    return salt.utils.win_system.join_domain(domain, username, password, account_ou, account_exists)


def unjoin_domain(
    username=None,
    password=None,
    domain=None,
    workgroup="WORKGROUP",
    disable=False,
    restart=False,
):
    # pylint: disable=anomalous-backslash-in-string
    """
    Unjoin a computer from an Active Directory Domain. Requires a restart.

    Args:

        username (str):
            Username of an account which is authorized to manage computer
            accounts on the domain. Needs to be a fully qualified name like
            ``user@domain.tld`` or ``domain.tld\\user``. If the domain is not
            specified, the passed domain will be used. If the computer account
            doesn't need to be disabled after the computer is unjoined, this can
            be ``None``.

        password (str):
            The password of the specified user

        domain (str):
            The domain from which to unjoin the computer. Can be ``None``

        workgroup (str):
            The workgroup to join the computer to. Default is ``WORKGROUP``

            .. versionadded:: 2015.8.2/2015.5.7

        disable (bool):
            ``True`` to disable the computer account in Active Directory.
            Default is ``False``

        restart (bool):
            ``True`` will restart the computer after successful unjoin. Default
            is ``False``

            .. versionadded:: 2015.8.2/2015.5.7

    Returns:
        dict: Returns a dictionary if successful, otherwise ``False``

    CLI Example:

    .. code-block:: bash

        salt 'minion-id' system.unjoin_domain restart=True

        salt 'minion-id' system.unjoin_domain username='unjoinuser' \\
                         password='unjoinpassword' disable=True \\
                         restart=True
    """
    return salt.utils.win_system.unjoin_domain(username, password, domain, workgroup, disable, restart)


def get_domain_workgroup():
    """
    Get the domain or workgroup the computer belongs to.

    .. versionadded:: 2015.5.7
    .. versionadded:: 2015.8.2

    Returns:
        str: The name of the domain or workgroup

    CLI Example:

    .. code-block:: bash

        salt 'minion-id' system.get_domain_workgroup
    """
    return salt.utils.win_system.get_domain_workgroup()


def set_domain_workgroup(workgroup):
    """
    Set the domain or workgroup the computer belongs to.

    .. versionadded:: 3001

    Returns:
        bool: ``True`` if successful, otherwise ``False``

    CLI Example:

    .. code-block:: bash

        salt 'minion-id' system.set_domain_workgroup LOCAL
    """
    return salt.utils.win_system.set_domain_workgroup(workgroup)


def get_system_time():
    """
    Get the system time.

    Returns:
        str: Returns the system time in HH:MM:SS AM/PM format.

    CLI Example:

    .. code-block:: bash

        salt 'minion-id' system.get_system_time
    """
    return salt.utils.win_system.get_system_time()


def set_system_time(newtime):
    """
    Set the system time.

    Args:

        newtime (str):
            The time to set. Can be any of the following formats:

            - HH:MM:SS AM/PM
            - HH:MM AM/PM
            - HH:MM:SS (24 hour)
            - HH:MM (24 hour)

    Returns:
        bool: ``True`` if successful, otherwise ``False``

    CLI Example:

    .. code-block:: bash

        salt 'minion-id' system.set_system_time 12:01
    """
    return salt.utils.win_system.set_system_time(newtime)


def set_system_date_time(
    years=None, months=None, days=None, hours=None, minutes=None, seconds=None
):
    """
    Set the system date and time. Each argument is an element of the date, but
    not required. If an element is not passed, the current system value for that
    element will be used. For example, if you don't pass the year, the current
    system year will be used. (Used by set_system_date and set_system_time)

    Args:

        years (int): Years digit, ie: 2015
        months (int): Months digit: 1 - 12
        days (int): Days digit: 1 - 31
        hours (int): Hours digit: 0 - 23
        minutes (int): Minutes digit: 0 - 59
        seconds (int): Seconds digit: 0 - 59

    Returns:
        bool: ``True`` if successful, otherwise ``False``

    CLI Example:

    .. code-block:: bash

        salt '*' system.set_system_date_ time 2015 5 12 11 37 53
    """
    return salt.utils.win_system.set_system_date_time(
        years, months, days, hours, minutes, seconds
    )


def get_system_date():
    """
    Get the Windows system date

    Returns:
        str: Returns the system date

    CLI Example:

    .. code-block:: bash

        salt '*' system.get_system_date
    """
    return salt.utils.win_system.get_system_date()


def set_system_date(newdate):
    """
    Set the Windows system date. Use <mm-dd-yy> format for the date.

    Args:
        newdate (str):
            The date to set. Can be any of the following formats

            - YYYY-MM-DD
            - MM-DD-YYYY
            - MM-DD-YY
            - MM/DD/YYYY
            - MM/DD/YY
            - YYYY/MM/DD

    Returns:
        bool: ``True`` if successful, otherwise ``False``

    CLI Example:

    .. code-block:: bash

        salt '*' system.set_system_date '03-28-13'
    """
    return salt.utils.win_system.set_system_date(newdate)


def start_time_service():
    """
    Start the Windows time service

    Returns:
        bool: ``True`` if successful, otherwise ``False``

    CLI Example:

    .. code-block:: bash

        salt '*' system.start_time_service
    """
    return __salt__["service.start"]("w32time")


def stop_time_service():
    """
    Stop the Windows time service

    Returns:
        bool: ``True`` if successful, otherwise ``False``

    CLI Example:

    .. code-block:: bash

        salt '*' system.stop_time_service
    """
    return __salt__["service.stop"]("w32time")


def get_pending_component_servicing():
    """
    Determine whether there are pending Component Based Servicing tasks that
    require a reboot.

    .. versionadded:: 2016.11.0

    Returns:
        bool: ``True`` if there are pending Component Based Servicing tasks,
        otherwise ``False``

    CLI Example:

    .. code-block:: bash

        salt '*' system.get_pending_component_servicing
    """
    return salt.utils.win_system._get_pending_component_servicing()


def get_pending_domain_join():
    """
    Determine whether there is a pending domain join action that requires a
    reboot.

    .. versionadded:: 2016.11.0

    Returns:
        bool: ``True`` if there is a pending domain join action, otherwise
        ``False``

    CLI Example:

    .. code-block:: bash

        salt '*' system.get_pending_domain_join
    """
    return salt.utils.win_system._get_pending_domain_join()


def get_pending_file_rename():
    """
    Determine whether there are pending file rename operations that require a
    reboot.

    .. versionadded:: 2016.11.0

    Returns:
        bool: ``True`` if there are pending file rename operations, otherwise
        ``False``

    CLI Example:

    .. code-block:: bash

        salt '*' system.get_pending_file_rename
    """
    return salt.utils.win_system._get_pending_file_rename()


def get_pending_servermanager():
    """
    Determine whether there are pending Server Manager tasks that require a
    reboot.

    .. versionadded:: 2016.11.0

    Returns:
        bool: ``True`` if there are pending Server Manager tasks, otherwise
        ``False``

    CLI Example:

    .. code-block:: bash

        salt '*' system.get_pending_servermanager
    """
    return salt.utils.win_system._get_pending_servermanager()


def get_pending_update():
    """
    Determine whether there are pending updates that require a reboot.

    .. versionadded:: 2016.11.0

    Returns:
        bool: ``True`` if there are pending updates, otherwise ``False``

    CLI Example:

    .. code-block:: bash

        salt '*' system.get_pending_update
    """
    return salt.utils.win_system._get_pending_update()


def set_reboot_required_witnessed():
    r"""
    This function is used to remember that an event indicating that a reboot is
    required was witnessed. This function relies on the salt-minion's ability to
    create the following volatile registry key in the *HKLM* hive:

       *SYSTEM\\CurrentControlSet\\Services\\salt-minion\\Volatile-Data*

    Because this registry key is volatile, it will not persist beyond the
    current boot session. Also, in the scope of this key, the name *'Reboot
    required'* will be assigned the value of *1*.

    For the time being, this function is being used whenever an install
    completes with exit code 3010 and can be extended where appropriate in the
    future.

    .. versionadded:: 2016.11.0

    Returns:
        bool: ``True`` if successful, otherwise ``False``

    CLI Example:

    .. code-block:: bash

        salt '*' system.set_reboot_required_witnessed
    """
    return salt.utils.win_system._set_reboot_required_witnessed()


def get_reboot_required_witnessed():
    """
    Determine if at any time during the current boot session the salt minion
    witnessed an event indicating that a reboot is required.

    This function will return ``True`` if an install completed with exit
    code 3010 during the current boot session and can be extended where
    appropriate in the future.

    .. versionadded:: 2016.11.0

    Returns:
        bool: ``True`` if the ``Requires reboot`` registry flag is set to ``1``,
        otherwise ``False``

    CLI Example:

    .. code-block:: bash

        salt '*' system.get_reboot_required_witnessed

    """
    return salt.utils.win_system._get_reboot_required_witnessed()


def get_pending_windows_update():
    """
    Check the Windows Update system for a pending reboot state.

    This leverages the Windows Update System to determine if the system is
    pending a reboot.

    .. versionadded:: 3001

    Returns:
        bool: ``True`` if the Windows Update system reports a pending update,
        otherwise ``False``

    CLI Example:

    .. code-block:: bash

        salt '*' system.get_pending_windows_update
    """
    return salt.utils.win_system._get_pending_windows_update()


def get_pending_reboot():
    """
    Determine whether there is a reboot pending.

    .. versionadded:: 2016.11.0

    Returns:
        bool: ``True`` if the system is pending reboot, otherwise ``False``

    CLI Example:

    .. code-block:: bash

        salt '*' system.get_pending_reboot
    """
    return salt.utils.win_system.get_pending_reboot()


def get_pending_reboot_details():
    """
    Determine which check is signalling that the system is pending a reboot.
    Useful in determining why your system is signalling that it needs a reboot.

    .. versionadded:: 3001

    Returns:
        dict: A dictionary of the results of each system that would indicate a
        pending reboot

    CLI Example:

    .. code-block:: bash

        salt '*' system.get_pending_reboot_details
    """
    return salt.utils.win_system.get_pending_reboot_details()
