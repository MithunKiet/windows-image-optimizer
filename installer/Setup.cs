using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Windows.Forms;
using Microsoft.Win32;

internal static class Setup
{
    private const string AppName = "CImageOptimizer";
    private const string Version = "1.0.0";

    [STAThread]
    private static int Main()
    {
        try
        {
            string localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            string desktop = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory);

            string installDir = Path.Combine(localAppData, "Programs", AppName);
            string startMenuDir = Path.Combine(appData, "Microsoft", "Windows", "Start Menu", "Programs", AppName);
            string exePath = Path.Combine(installDir, AppName + ".exe");
            string uninstallPath = Path.Combine(installDir, "Uninstall-CImageOptimizer.ps1");

            Directory.CreateDirectory(installDir);
            Directory.CreateDirectory(startMenuDir);

            ExtractResource("CImageOptimizer.exe", exePath);
            ExtractResource("Uninstall-CImageOptimizer.ps1", uninstallPath);

            CreateShortcut(Path.Combine(startMenuDir, AppName + ".lnk"), exePath, installDir, exePath);
            CreateShortcut(Path.Combine(desktop, AppName + ".lnk"), exePath, installDir, exePath);
            CreateUninstallShortcut(Path.Combine(startMenuDir, "Uninstall " + AppName + ".lnk"), uninstallPath, installDir);
            RegisterUninstaller(installDir, exePath, uninstallPath);

            MessageBox.Show(AppName + " has been installed.", AppName, MessageBoxButtons.OK, MessageBoxIcon.Information);
            Process.Start(new ProcessStartInfo { FileName = exePath, WorkingDirectory = installDir });
            return 0;
        }
        catch (Exception ex)
        {
            MessageBox.Show("Installation failed:\r\n" + ex.Message, AppName + " Installer", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }

    private static void ExtractResource(string resourceName, string destinationPath)
    {
        using (Stream input = Assembly.GetExecutingAssembly().GetManifestResourceStream(resourceName))
        {
            if (input == null)
            {
                throw new InvalidOperationException("Installer resource is missing: " + resourceName);
            }

            using (FileStream output = File.Create(destinationPath))
            {
                input.CopyTo(output);
            }
        }
    }

    private static void CreateShortcut(string shortcutPath, string targetPath, string workingDirectory, string iconPath)
    {
        string script =
            "$shell = New-Object -ComObject WScript.Shell\r\n" +
            "$shortcut = $shell.CreateShortcut(" + PsQuote(shortcutPath) + ")\r\n" +
            "$shortcut.TargetPath = " + PsQuote(targetPath) + "\r\n" +
            "$shortcut.WorkingDirectory = " + PsQuote(workingDirectory) + "\r\n" +
            "$shortcut.IconLocation = " + PsQuote(iconPath + ",0") + "\r\n" +
            "$shortcut.Save()\r\n";

        RunPowerShell(script);
    }

    private static void CreateUninstallShortcut(string shortcutPath, string uninstallScript, string workingDirectory)
    {
        string script =
            "$shell = New-Object -ComObject WScript.Shell\r\n" +
            "$shortcut = $shell.CreateShortcut(" + PsQuote(shortcutPath) + ")\r\n" +
            "$shortcut.TargetPath = 'powershell.exe'\r\n" +
            "$shortcut.Arguments = " + PsQuote("-NoProfile -ExecutionPolicy Bypass -File \"" + uninstallScript + "\"") + "\r\n" +
            "$shortcut.WorkingDirectory = " + PsQuote(workingDirectory) + "\r\n" +
            "$shortcut.IconLocation = 'powershell.exe,0'\r\n" +
            "$shortcut.Save()\r\n";

        RunPowerShell(script);
    }

    private static void RegisterUninstaller(string installDir, string exePath, string uninstallPath)
    {
        using (RegistryKey key = Registry.CurrentUser.CreateSubKey(@"Software\Microsoft\Windows\CurrentVersion\Uninstall\" + AppName))
        {
            key.SetValue("DisplayName", AppName, RegistryValueKind.String);
            key.SetValue("DisplayIcon", exePath, RegistryValueKind.String);
            key.SetValue("DisplayVersion", Version, RegistryValueKind.String);
            key.SetValue("Publisher", AppName, RegistryValueKind.String);
            key.SetValue("InstallLocation", installDir, RegistryValueKind.String);
            key.SetValue("UninstallString", "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"" + uninstallPath + "\"", RegistryValueKind.String);
            key.SetValue("NoModify", 1, RegistryValueKind.DWord);
            key.SetValue("NoRepair", 1, RegistryValueKind.DWord);
        }
    }

    private static void RunPowerShell(string script)
    {
        string tempScript = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString("N") + ".ps1");
        File.WriteAllText(tempScript, script);

        try
        {
            ProcessStartInfo startInfo = new ProcessStartInfo
            {
                FileName = "powershell.exe",
                Arguments = "-NoProfile -ExecutionPolicy Bypass -File \"" + tempScript + "\"",
                CreateNoWindow = true,
                UseShellExecute = false,
                WindowStyle = ProcessWindowStyle.Hidden
            };

            using (Process process = Process.Start(startInfo))
            {
                process.WaitForExit();
                if (process.ExitCode != 0)
                {
                    throw new InvalidOperationException("PowerShell shortcut creation failed.");
                }
            }
        }
        finally
        {
            try
            {
                File.Delete(tempScript);
            }
            catch
            {
            }
        }
    }

    private static string PsQuote(string value)
    {
        return "'" + value.Replace("'", "''") + "'";
    }
}
